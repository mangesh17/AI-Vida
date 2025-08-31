export default function BackendDiagrams() {
  return (
    <div className="p-6 space-y-10 bg-white text-gray-900">
      {/* Title */}
      <h1 className="text-2xl font-bold">Aivida Discharge Copilot — Backend (Cloud‑Agnostic)</h1>

      {/* C4 Container Diagram */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">1) C4 Container Diagram (Cloud‑Agnostic)</h2>
        <div className="w-full overflow-auto rounded-2xl border shadow-sm">
          <svg viewBox="0 0 1400 880" className="w-full h-auto">
            {/* Background */}
            <rect x="0" y="0" width="1400" height="880" rx="24" fill="#f8fafc"/>

            {/* Clients */}
            <g>
              <rect x="40" y="40" width="390" height="200" rx="16" fill="#ffffff" stroke="#cbd5e1"/>
              <text x="60" y="80" className="fill-current" fontSize="18" fontWeight="700">Clients</text>
              <rect x="60" y="100" width="160" height="46" rx="10" fill="#eef2ff" stroke="#c7d2fe"/>
              <text x="70" y="128" fontSize="14">Patient UI</text>
              <rect x="230" y="100" width="160" height="46" rx="10" fill="#eef2ff" stroke="#c7d2fe"/>
              <text x="240" y="128" fontSize="14">Clinician UI</text>
              <rect x="60" y="154" width="160" height="46" rx="10" fill="#eef2ff" stroke="#c7d2fe"/>
              <text x="70" y="182" fontSize="14">Admin UI</text>
              <rect x="230" y="154" width="160" height="46" rx="10" fill="#eef2ff" stroke="#c7d2fe"/>
              <text x="240" y="182" fontSize="14">Auth (OTP/SSO)</text>
            </g>

            {/* API Gateway */}
            <g>
              <rect x="470" y="60" width="220" height="60" rx="12" fill="#ffffff" stroke="#94a3b8"/>
              <text x="520" y="98" fontSize="16" fontWeight="700">API GW</text>
            </g>

            {/* Core Services Box */}
            <g>
              <rect x="430" y="140" width="520" height="360" rx="16" fill="#ffffff" stroke="#cbd5e1"/>
              <text x="450" y="170" fontSize="16" fontWeight="700">Core Services</text>

              {/* Row 1 */}
              <rect x="450" y="190" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="470" y="226" fontSize="14">Ingest</text>
              <rect x="610" y="190" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="632" y="226" fontSize="14">Normalize</text>
              <rect x="770" y="190" width="160" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="792" y="226" fontSize="14">Rules</text>

              {/* Row 2 */}
              <rect x="450" y="260" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="472" y="296" fontSize="14">Gen</text>
              <rect x="610" y="260" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="640" y="296" fontSize="14">Chat</text>
              <rect x="770" y="260" width="160" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="790" y="296" fontSize="14">Config</text>

              {/* Row 3 */}
              <rect x="450" y="330" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="470" y="366" fontSize="14">AuthZ</text>
              <rect x="610" y="330" width="150" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="640" y="366" fontSize="14">Audit</text>
              <rect x="770" y="330" width="160" height="60" rx="10" fill="#ecfeff" stroke="#a5f3fc"/>
              <text x="792" y="366" fontSize="14">PDF/ICS</text>

              {/* Row 4 */}
              <rect x="450" y="400" width="480" height="80" rx="10" fill="#f1f5f9" stroke="#cbd5e1"/>
              <text x="470" y="430" fontSize="14">Observability</text>
              <text x="600" y="430" fontSize="14">• Metrics • Logs • Traces</text>
              <text x="470" y="450" fontSize="14">Ops Dashboard</text>
            </g>

            {/* Data & Infra */}
            <g>
              <rect x="380" y="520" width="640" height="180" rx="16" fill="#ffffff" stroke="#cbd5e1"/>
              <text x="400" y="550" fontSize="16" fontWeight="700">Data & Infra (Cloud‑Agnostic)</text>

              <rect x="400" y="570" width="160" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="415" y="604" fontSize="14">ObjStore</text>

              <rect x="570" y="570" width="160" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="597" y="604" fontSize="14">RDBMS</text>

              <rect x="740" y="570" width="140" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="762" y="604" fontSize="14">Search</text>

              <rect x="890" y="570" width="110" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="910" y="604" fontSize="14">Queue</text>

              <rect x="400" y="630" width="160" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="430" y="664" fontSize="14">Secrets/KMS</text>

              <rect x="570" y="630" width="160" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="600" y="664" fontSize="14">CI/CD</text>

              <rect x="740" y="630" width="260" height="56" rx="10" fill="#fefce8" stroke="#fde68a"/>
              <text x="760" y="664" fontSize="14">Kubernetes/Containers</text>
            </g>

            {/* External Systems */}
            <g>
              <rect x="1000" y="40" width="360" height="200" rx="16" fill="#ffffff" stroke="#cbd5e1"/>
              <text x="1020" y="70" fontSize="16" fontWeight="700">External Systems</text>

              <rect x="1020" y="90" width="150" height="46" rx="10" fill="#ffe4e6" stroke="#fecdd3"/>
              <text x="1034" y="118" fontSize="13">EHR (FHIR/HL7)</text>

              <rect x="1180" y="90" width="160" height="46" rx="10" fill="#ffe4e6" stroke="#fecdd3"/>
              <text x="1198" y="118" fontSize="13">LLM Provider</text>

              <rect x="1020" y="144" width="150" height="46" rx="10" fill="#ffe4e6" stroke="#fecdd3"/>
              <text x="1038" y="172" fontSize="13">OCR</text>

              <rect x="1180" y="144" width="160" height="46" rx="10" fill="#ffe4e6" stroke="#fecdd3"/>
              <text x="1194" y="172" fontSize="13">Translation</text>
            </g>

            {/* Arrows */}
            {/* Clients -> API GW */}
            <line x1="430" y1="120" x2="470" y2="90" stroke="#64748b" markerEnd="url(#arrow)"/>
            {/* API GW -> Core Services */}
            <line x1="580" y1="120" x2="580" y2="140" stroke="#64748b" markerEnd="url(#arrow)"/>
            {/* Core Services -> Data & Infra */}
            <line x1="690" y1="500" x2="690" y2="520" stroke="#64748b" markerEnd="url(#arrow)"/>
            {/* Core Services <-> External */}
            <line x1="950" y1="240" x2="1000" y2="160" stroke="#64748b" markerEnd="url(#arrow)"/>
            <line x1="950" y1="240" x2="1000" y2="110" stroke="#64748b" markerEnd="url(#arrow)"/>
            <line x1="950" y1="290" x2="1000" y2="185" stroke="#64748b" markerEnd="url(#arrow)"/>

            {/* Arrow Marker */}
            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L6,3 z" fill="#64748b" />
              </marker>
            </defs>
          </svg>
        </div>

        {/* Legend */}
        <div className="text-sm leading-6 text-gray-700">
          <h3 className="font-semibold">Legend (Short → Description)</h3>
          <ul className="list-disc pl-6">
            <li><strong>API GW</strong> → API Gateway / Edge routing, auth, rate limits.</li>
            <li><strong>Ingest</strong> → Intake PDFs/text, FHIR, HL7, CSV; OCR when needed.</li>
            <li><strong>Normalize</strong> → Structure + map meds (RxNorm), appts, diet/activity.</li>
            <li><strong>Rules</strong> → Units/frequency mapping; schedule rendering; checks.</li>
            <li><strong>Gen</strong> → Instruction generation (grounded, multilingual).</li>
            <li><strong>Chat</strong> → Document-grounded Q&A with safety guardrails.</li>
            <li><strong>Config</strong> → Site settings, data-source mappings, locales.</li>
            <li><strong>AuthZ</strong> → RBAC/SSO integration for pilot; patient/clinician/admin.</li>
            <li><strong>Audit</strong> → Access trails; PHI-minimized logs.</li>
            <li><strong>PDF/ICS</strong> → Packet rendering & calendar export (PHI-minimized).</li>
            <li><strong>ObjStore</strong> → Original docs & generated PDFs.</li>
            <li><strong>RDBMS</strong> → Episode state & normalized facts.</li>
            <li><strong>Search</strong> → Episode-scoped grounding index.</li>
            <li><strong>Queue</strong> → Async pipelines (OCR, LLM, translation, rendering).</li>
            <li><strong>Secrets/KMS</strong> → Secrets mgmt + encryption keys.</li>
            <li><strong>CI/CD</strong> → Build & deploy automation (vendor-agnostic).</li>
            <li><strong>Kubernetes/Containers</strong> → Portable runtime across clouds.</li>
            <li><strong>EHR (FHIR/HL7)</strong> → Read-only integrations for pilot.</li>
            <li><strong>LLM/OCR/Translation</strong> → Pluggable providers (no vendor lock).</li>
          </ul>
        </div>
      </section>

      {/* Sequence Diagram */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold">2) Sequence Flow: PDF → Packet → Approve → Publish → Patient</h2>
        <div className="w-full overflow-auto rounded-2xl border shadow-sm">
          <svg viewBox="0 0 1400 720" className="w-full h-auto">
            <rect x="0" y="0" width="1400" height="720" rx="24" fill="#f8fafc"/>

            {/* Lifelines */}
            {[
              { x: 80, label: 'Clinician UI' },
              { x: 300, label: 'API GW' },
              { x: 520, label: 'Ingest/Normalize' },
              { x: 780, label: 'Gen/Rules' },
              { x: 1000, label: 'Storage' },
              { x: 1220, label: 'Patient UI' },
            ].map(({ x, label }, i) => (
              <g key={i}>
                <rect x={x - 70} y={30} width={140} height={34} rx={8} fill="#ffffff" stroke="#cbd5e1"/>
                <text x={x - 60} y={52} fontSize="14">{label}</text>
                <line x1={x} y1={70} x2={x} y2={680} stroke="#94a3b8" strokeDasharray="6 6"/>
              </g>
            ))}

            {/* Messages */}
            const msg = (x1, x2, y, text) => (
              <g>
                <line x1={x1} y1={y} x2={x2} y2={y} stroke="#64748b" markerEnd="url(#arrow)"/>
                <text x={(x1+x2)/2 - 120} y={y - 8} fontSize="13">{text}</text>
              </g>
            )

            {/* Steps */}
            <g>
              {/* 1 Upload PDF */}
              <line x1="80" y1="110" x2="300" y2="110" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="120" y="98" fontSize="13">1) Upload discharge PDF</text>

              {/* 2 GW -> Ingest */}
              <line x1="300" y1="150" x2="520" y2="150" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="320" y="138" fontSize="13">2) Route & auth</text>

              {/* 3 OCR/Parse */}
              <line x1="520" y1="190" x2="780" y2="190" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="530" y="178" fontSize="13">3) OCR + Section parse</text>

              {/* 4 Normalize */}
              <line x1="520" y1="230" x2="1000" y2="230" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="560" y="218" fontSize="13">4) Normalize meds/appts/diet → store</text>

              {/* 5 Generate draft */}
              <line x1="300" y1="270" x2="780" y2="270" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="360" y="258" fontSize="13">5) Generate patient-friendly draft</text>

              {/* 6 Apply rules */}
              <line x1="780" y1="310" x2="1000" y2="310" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="800" y="298" fontSize="13">6) Units/frequency mapping</text>

              {/* 7 Fetch draft for review */}
              <line x1="300" y1="350" x2="80" y2="350" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="120" y="338" fontSize="13">7) Return draft for review</text>

              {/* 8 Approve & publish */}
              <line x1="80" y1="390" x2="300" y2="390" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="120" y="378" fontSize="13">8) Approve & publish</text>

              <line x1="300" y1="430" x2="1000" y2="430" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="520" y="418" fontSize="13">9) Persist packet + PDF</text>

              {/* 10 Patient access */}
              <line x1="1220" y1="470" x2="300" y2="470" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="1020" y="458" fontSize="13">10) Patient requests packet</text>

              <line x1="300" y1="510" x2="1220" y2="510" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="880" y="498" fontSize="13">11) Packet/translated view</text>

              {/* 12 Download ICS */}
              <line x1="1220" y1="550" x2="300" y2="550" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="1030" y="538" fontSize="13">12) Download appts .ics</text>

              {/* 13 Chat Q&A */}
              <line x1="1220" y1="590" x2="300" y2="590" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="1040" y="578" fontSize="13">13) Chat (grounded)</text>

              <line x1="300" y1="630" x2="780" y2="630" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="480" y="618" fontSize="13">14) Retrieve answers (scoped)</text>

              <line x1="780" y1="670" x2="1220" y2="670" stroke="#64748b" markerEnd="url(#arrow)"/>
              <text x="980" y="658" fontSize="13">15) Respond w/ citations</text>
            </g>

            <defs>
              <marker id="arrow" markerWidth="10" markerHeight="10" refX="6" refY="3" orient="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L6,3 z" fill="#64748b" />
              </marker>
            </defs>
          </svg>
        </div>

        {/* Notes / Legend */}
        <div className="text-sm leading-6 text-gray-700">
          <h3 className="font-semibold">Notes</h3>
          <ul className="list-disc pl-6">
            <li>All components are <strong>cloud‑agnostic</strong>. Map to any vendor: ObjStore (e.g., S3/Blob/GS), RDBMS (Postgres/MySQL), Queue (SQS/Queue/PS), Search (OpenSearch/Elastic), KMS (KMS/KeyVault/Cloud KMS), Containers (EKS/AKS/GKE/On‑prem K8s).</li>
            <li>LLM/OCR/Translation are pluggable providers; no single‑vendor dependency.</li>
            <li>Sequence emphasizes <strong>grounded generation</strong>, clinician review, and PHI‑minimized outputs.</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
