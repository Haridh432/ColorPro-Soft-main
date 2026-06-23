import uuid
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from rest_framework import status
from rest_framework.test import APITestCase
from core.models import Batch, Roll, Scan, ComparisonResult, Report
from core.services.comparison_service import compare_batch, run_quality_gate
from core.services.clustering_service import cluster_shade_groups
from core.services.report_service import generate_report

class PerformanceQueryCountTests(APITestCase):
    def setUp(self):
        # Create user
        self.user = User.objects.create_user(username='qc_manager', password='password123')
        self.client.force_authenticate(user=self.user)

        # Create a batch
        self.batch = Batch.objects.create(
            name="Batch-001",
            description="Test Batch",
            client_l=50.0,
            client_a=10.0,
            client_b=15.0
        )

        # Create multiple rolls with scans
        self.rolls = []
        for i in range(5):
            roll = Roll.objects.create(
                batch=self.batch,
                roll_number=f"R-00{i+1}",
                order=i,
                avg_l=50.0 + (i * 0.1),
                avg_a=10.0,
                avg_b=15.0,
                status='scanned'
            )
            self.rolls.append(roll)
            # Create a scan for each roll
            Scan.objects.create(
                roll=roll,
                r=128, g=128, b=128,
                l_val=50.0 + (i * 0.1),
                a_val=10.0,
                b_val=15.0
            )

    def test_batch_list_query_count(self):
        """
        Verify that listing batches does not trigger N+1 queries.
        We check that listing 1 batch vs 5 batches results in the same, minimal number of queries.
        """
        # Create 4 more batches with rolls
        for k in range(4):
            b = Batch.objects.create(name=f"Batch-00{k+2}")
            for i in range(3):
                Roll.objects.create(
                    batch=b,
                    roll_number=f"R-{k+2}-00{i+1}",
                    order=i,
                    avg_l=50.0, avg_a=10.0, avg_b=15.0,
                    status='scanned'
                )

        url = reverse('batch-list')

        # We assert that serialization of batches does not trigger queries for each batch's roll count properties,
        # thanks to annotations in the viewset's get_queryset.
        with self.assertNumQueries(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_batch_rolls_prefetched_query_count(self):
        """
        Verify that getting rolls of a batch fetches scans in a prefetched manner.
        # Expect exactly 3 queries: one to fetch the batch (get_object), one to fetch rolls, one to prefetch scans
        """
        url = reverse('batch-rolls', kwargs={'pk': self.batch.id})

        with self.assertNumQueries(3):
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(len(response.data), 5)
            # Check that avg_rgb and scan_count are present
            self.assertEqual(response.data[0]['scan_count'], 1)
            self.assertIsNotNone(response.data[0]['avg_rgb'])

    def test_bulk_create_rolls_performance(self):
        """
        Verify bulk roll creation endpoint performs a single bulk_create and minimal query footprint.
        """
        url = reverse('roll-bulk-create')
        data = {
            "batch_id": str(self.batch.id),
            "roll_numbers": ["R-101", "R-102", "R-103", "R-104", "R-105"]
        }

        # 1. Fetch batch (1 query)
        # 2. Check existing rolls matching numbers (1 query)
        # 3. Bulk create rolls (1 query)
        # 4. Fetch all rolls for response (1 query)
        # 5. Prefetch scans (1 query)
        # Total should be exactly 5 queries. Without bulk_create it would be at least 15.
        with self.assertNumQueries(5):
            response = self.client.post(url, data, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            self.assertEqual(len(response.data), 5)

    def test_comparison_service_bulk_create(self):
        """
        Verify compare_batch service function runs bulk_create on ComparisonResult,
        minimizing queries to compute pairwise differences.
        """
        self.assertTrue(len(self.rolls) >= 2)
        ComparisonResult.objects.filter(batch=self.batch).delete()

        with self.assertNumQueries(4):
            results = compare_batch(self.batch.id)

        self.assertEqual(len(results), 10)
        self.assertEqual(ComparisonResult.objects.filter(batch=self.batch).count(), 10)

    def test_quality_gate_bulk_update(self):
        """
        Verify that run_quality_gate updates all rolls status and delta_e using bulk_update.
        """
        with self.assertNumQueries(3):
            result = run_quality_gate(self.batch.id)
        self.assertEqual(len(result['accepted']) + len(result['warning']) + len(result['rejected']), 5)

    def test_clustering_service_bulk_update(self):
        """
        Verify that cluster_shade_groups performs a single bulk_update.
        """
        run_quality_gate(self.batch.id)

        with self.assertNumQueries(3):
            groups = cluster_shade_groups(self.batch.id)
        self.assertTrue(len(groups) > 0)

    def test_report_service_query_footprint(self):
        """
        Verify that generate_report loads rolls and comparison results eagerly.
        """
        compare_batch(self.batch.id)
        run_quality_gate(self.batch.id)

        if not hasattr(settings, 'BRAND_NAME'):
            settings.BRAND_NAME = "ColorPro"

        with self.assertNumQueries(6):
            report = generate_report(self.batch.id, user=self.user)
            self.assertIsNotNone(report.pdf_file)
            self.assertEqual(report.status, 'draft')
