'use client';

export default function ColorSwatch({ rgb, size = 36, showLabel = false, lab = null }) {
  if (!rgb || rgb.length < 3) {
    return (
      <div
        className="rounded-lg border-2 border-dashed border-slate-600 flex items-center justify-center"
        style={{ width: size, height: size }}
      >
        <span className="text-slate-600 text-xs">—</span>
      </div>
    );
  }

  const bgColor = `rgb(${rgb[0]}, ${rgb[1]}, ${rgb[2]})`;
  const hexHex = '#' + rgb.map(x => {
    const hex = x.toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  }).join('').toUpperCase();

  return (
    <div className="flex items-center gap-2">
      <div
        className="color-swatch"
        style={{
          backgroundColor: bgColor,
          width: size,
          height: size,
        }}
        title={`RGB(${rgb.join(', ')})${lab ? ` | LAB(${lab.l?.toFixed(1)}, ${lab.a?.toFixed(1)}, ${lab.b?.toFixed(1)})` : ''}`}
      />
      {showLabel && (
        <div className="text-[10px]">
          <div className="text-slate-300 font-mono font-bold tracking-wide mb-0.5">
            {hexHex}
          </div>
          <div className="text-slate-500 font-mono leading-none">
            ({rgb[0]}, {rgb[1]}, {rgb[2]})
          </div>
          {lab && (
            <div className="text-slate-500 font-mono mt-0.5 leading-none">
              L:{lab.l?.toFixed(1)} a:{lab.a?.toFixed(1)} b:{lab.b?.toFixed(1)}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
