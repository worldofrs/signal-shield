type CellContent = string | "check" | "cross";

const ROWS: { capability: string; reactive: CellContent; shield: CellContent }[] = [
  { capability: "Approach", reactive: "Detect deepfakes after they spread", shield: "Prevent cloning before it happens" },
  { capability: "Stops voice cloning", reactive: "cross", shield: "check" },
  { capability: "Audio sounds the same", reactive: "cross", shield: "check" },
  { capability: "Works against multiple AI models", reactive: "cross", shield: "check" },
  { capability: "Pricing", reactive: "Enterprise contracts", shield: "Free tier + pay as you go" },
  { capability: "No quality loss", reactive: "cross", shield: "check" },
  { capability: "Simple upload workflow", reactive: "cross", shield: "check" },
];

const CheckIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M5 10L9 14L15 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const CrossIcon = () => (
  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
    <path d="M6 6L14 14M14 6L6 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

function renderCell(content: CellContent, isShield: boolean) {
  if (content === "check") {
    return (
      <span className={isShield ? "text-accent" : "text-accent"}>
        <CheckIcon />
      </span>
    );
  }
  if (content === "cross") {
    return (
      <span className="text-text-muted">
        <CrossIcon />
      </span>
    );
  }
  return <span>{content}</span>;
}

export default function Comparison() {
  return (
    <section className="py-28 bg-[#f7f7f5]">
      <div className="max-w-[1200px] mx-auto px-8">
        <div className="mb-14">
          <p className="text-[11.5px] font-normal text-accent uppercase tracking-[2.3px] mb-6 font-mono">
            Why SignalShield
          </p>
          <h2 className="text-[clamp(2rem,4vw,3.6rem)] font-normal text-text-heading leading-[1] tracking-[-1.5px]">
            Competitors detect.
            <br />
            We prevent.
          </h2>
        </div>

        <div className="overflow-x-auto rounded-2xl border border-[#e5e5e0] bg-white">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="text-left text-xs font-normal text-text-body uppercase tracking-[0.6px] p-5 bg-[#e0edef] w-1/3 font-mono">
                  Capability
                </th>
                <th className="text-left text-xs font-normal text-text-body uppercase tracking-[0.6px] p-5 bg-[#e0edef] border-l border-[#0d3957] w-1/3 font-mono">
                  Reactive tools
                </th>
                <th className="text-left text-xs font-normal text-white uppercase tracking-[0.6px] p-5 bg-[#0d3957] w-1/3 font-mono">
                  SignalShield
                </th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map(({ capability, reactive, shield }) => (
                <tr key={capability} className="border-t border-[#e5e5e0]">
                  <td className="text-sm text-text-heading p-5">
                    {capability}
                  </td>
                  <td className="text-sm text-text-body p-5 border-l border-[#e5e5e0]">
                    {renderCell(reactive, false)}
                  </td>
                  <td className="text-sm text-text-heading p-5 bg-[rgba(10,37,64,0.03)] border-l border-[#e5e5e0]">
                    {renderCell(shield, true)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
