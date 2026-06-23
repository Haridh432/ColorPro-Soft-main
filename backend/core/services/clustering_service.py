"""
ML-based shade clustering service.

Groups accepted rolls into shade sub-groups using LAB values.
Uses Agglomerative Clustering with automatic cluster count selection,
falling back to DBSCAN for small batches.
"""

import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans
from sklearn.metrics import silhouette_score

from core.models import Batch, Roll


def cluster_shade_groups(batch_id):
    """
    Run ML clustering on accepted + warning rolls to group similar shades.

    Process:
    1. Collect LAB values of all accepted + warning rolls
    2. Try Agglomerative Clustering with 2 to N/2 clusters
    3. Select best cluster count using silhouette score
    4. Falls back to DBSCAN if fewer than 5 rolls
    5. Assign shade group numbers (1, 2, 3...)

    Returns:
        Dict mapping group number → list of Roll instances
    """
    batch = Batch.objects.get(id=batch_id)
    rolls = list(batch.rolls.filter(
        status__in=['accepted', 'warning'],
        avg_l__isnull=False
    ))

    if len(rolls) < 2:
        # Single roll or no rolls — assign all to group 1
        for roll in rolls:
            roll.shade_group = 1
        if rolls:
            Roll.objects.bulk_update(rolls, ['shade_group'])
        return {1: rolls} if rolls else {}

    # Build LAB feature matrix
    lab_matrix = np.array([
        [r.avg_l, r.avg_a, r.avg_b] for r in rolls
    ])

    if len(rolls) < 5:
        # Small batch — use DBSCAN with small epsilon
        labels = _cluster_dbscan(lab_matrix)
    else:
        # Larger batch — use Agglomerative with silhouette optimization
        labels = _cluster_agglomerative(lab_matrix)

    # Assign shade groups (convert labels to 1-indexed)
    groups = {}
    for roll, label in zip(rolls, labels):
        group_num = int(label) + 1  # 1-indexed
        roll.shade_group = group_num

        if group_num not in groups:
            groups[group_num] = []
        groups[group_num].append(roll)

    if rolls:
        Roll.objects.bulk_update(rolls, ['shade_group'])

    return dict(sorted(groups.items()))



def _cluster_agglomerative(lab_matrix):
    """
    Agglomerative clustering with automatic cluster count selection.
    Tries 2 to min(N/2, 10) clusters and picks the best silhouette score.
    """
    n_samples = len(lab_matrix)
    max_clusters = min(n_samples // 2, 10)
    max_clusters = max(max_clusters, 2)

    best_score = -1
    best_labels = None

    for n_clusters in range(2, max_clusters + 1):
        try:
            clustering = AgglomerativeClustering(
                n_clusters=n_clusters,
                metric='euclidean',
                linkage='ward'
            )
            labels = clustering.fit_predict(lab_matrix)

            # Skip if all samples are in one cluster
            if len(set(labels)) < 2:
                continue

            score = silhouette_score(lab_matrix, labels)
            if score > best_score:
                best_score = score
                best_labels = labels
        except Exception:
            continue

    # Fallback: if no good clustering found, put all in one group
    if best_labels is None:
        return np.zeros(n_samples, dtype=int)

    return best_labels


def _cluster_dbscan(lab_matrix):
    """
    DBSCAN clustering for small batches.
    Uses a small epsilon since LAB differences in textiles are typically small.
    """
    clustering = DBSCAN(
        eps=0.3,  # Small ΔE threshold for tight grouping
        min_samples=1,
        metric='euclidean'
    )
    labels = clustering.fit_predict(lab_matrix)

    # DBSCAN assigns -1 to noise; remap to 0
    labels = np.where(labels == -1, 0, labels)

    return labels

def _cluster_kmeans(lab_matrix, n_clusters):
    """
    KMeans clustering.
    """
    if n_clusters > len(lab_matrix):
        n_clusters = len(lab_matrix)
    if n_clusters < 1:
        n_clusters = 1
    
    clustering = KMeans(n_clusters=n_clusters, random_state=42)
    labels = clustering.fit_predict(lab_matrix)
    return labels

def cluster_shade_groups_advanced(batch_id, method='auto', n_clusters=None, eps=0.3):
    """
    Run ML clustering on accepted + warning rolls to group similar shades with advanced configuration.
    """
    batch = Batch.objects.get(id=batch_id)
    rolls = list(batch.rolls.filter(
        status__in=['accepted', 'warning'],
        avg_l__isnull=False
    ))

    if len(rolls) < 2:
        for roll in rolls:
            roll.shade_group = 1
        if rolls:
            Roll.objects.bulk_update(rolls, ['shade_group'])
        return {1: rolls} if rolls else {}

    # Build LAB feature matrix
    lab_matrix = np.array([
        [r.avg_l, r.avg_a, r.avg_b] for r in rolls
    ])

    if method == 'kmeans':
        if not n_clusters:
            n_clusters = min(len(rolls) // 2, 3)
            n_clusters = max(n_clusters, 2)
        labels = _cluster_kmeans(lab_matrix, int(n_clusters))
    elif method == 'dbscan':
        clustering = DBSCAN(eps=float(eps), min_samples=1, metric='euclidean')
        labels = clustering.fit_predict(lab_matrix)
        labels = np.where(labels == -1, 0, labels)
    else:
        # Auto or agglomerative
        if len(rolls) < 5:
            labels = _cluster_dbscan(lab_matrix)
        else:
            labels = _cluster_agglomerative(lab_matrix)

    # Assign shade groups (convert labels to 1-indexed)
    groups = {}
    for roll, label in zip(rolls, labels):
        group_num = int(label) + 1
        roll.shade_group = group_num

        if group_num not in groups:
            groups[group_num] = []
        groups[group_num].append(roll)

    if rolls:
        Roll.objects.bulk_update(rolls, ['shade_group'])

    return dict(sorted(groups.items()))

