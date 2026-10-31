import xml.etree.ElementTree as ET

def generate_activity_diagram():
    svg = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1520 1340" width="100%" height="100%">
  <defs>
    <style><![CDATA[
      .diagram-bg { fill: #F8FAFC; }
      .header-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 21px; font-weight: 700; fill: #0F172A; }
      .header-subtitle { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: 400; fill: #475569; }

      /* Swimlane Styles */
      .lane-bg-1 { fill: #FFFFFF; stroke: #CBD5E1; stroke-width: 1.2; }
      .lane-bg-2 { fill: #FBFBFF; stroke: #CBD5E1; stroke-width: 1.2; }
      .lane-bg-3 { fill: #F6FEF9; stroke: #CBD5E1; stroke-width: 1.2; }
      .lane-bg-4 { fill: #FFFDF7; stroke: #CBD5E1; stroke-width: 1.2; }
      
      .lane-header-1 { fill: #1E40AF; }
      .lane-header-2 { fill: #4338CA; }
      .lane-header-3 { fill: #047857; }
      .lane-header-4 { fill: #B45309; }
      
      .lane-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 13px; font-weight: 700; fill: #FFFFFF; text-anchor: middle; }
      .lane-sub { font-family: 'Consolas', 'Courier New', monospace; font-size: 10px; fill: #E0E7FF; text-anchor: middle; }
      .lane-sub-green { font-family: 'Consolas', 'Courier New', monospace; font-size: 10px; fill: #D1FAE5; text-anchor: middle; }
      .lane-sub-amber { font-family: 'Consolas', 'Courier New', monospace; font-size: 10px; fill: #FEF3C7; text-anchor: middle; }

      /* Activity Nodes */
      .act-node { fill: #FFFFFF; stroke: #3B82F6; stroke-width: 1.5; rx: 16; ry: 16; }
      .act-node-purple { fill: #FFFFFF; stroke: #6366F1; stroke-width: 1.5; rx: 16; ry: 16; }
      .act-node-emerald { fill: #FFFFFF; stroke: #10B981; stroke-width: 1.5; rx: 16; ry: 16; }
      .act-node-amber { fill: #FFFFFF; stroke: #F59E0B; stroke-width: 1.5; rx: 16; ry: 16; }
      
      .act-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11px; font-weight: 700; fill: #0F172A; text-anchor: middle; }
      .act-detail { font-family: 'Consolas', 'Courier New', monospace; font-size: 9.5px; fill: #475569; text-anchor: middle; }

      /* Decision / Merge Diamond */
      .decision-node { fill: #FEF3C7; stroke: #D97706; stroke-width: 1.5; }
      .decision-label { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.5px; font-weight: 600; fill: #78350F; text-anchor: middle; }
      .guard-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10px; font-weight: 700; fill: #0369A1; }
      .guard-text-amber { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10px; font-weight: 700; fill: #B45309; }

      /* Synchronization Bar (Fork / Join) */
      .sync-bar { fill: #1E293B; stroke: #0F172A; stroke-width: 1; rx: 2; ry: 2; }
      .sync-label { font-family: 'Segoe UI', Arial, sans-serif; font-size: 9.5px; font-weight: 700; fill: #64748B; letter-spacing: 0.5px; }

      /* Flow Edges */
      .flow-line { stroke: #334155; stroke-width: 1.6; fill: none; }
      
      /* Legend */
      .legend-box { fill: #FFFFFF; stroke: #E2E8F0; stroke-width: 1.2; rx: 8; ry: 8; }
      .legend-title { font-family: 'Segoe UI', Arial, sans-serif; font-size: 11.5px; font-weight: 700; fill: #334155; }
      .legend-text { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10.5px; fill: #64748B; }
    ]]></style>

    <marker id="flow-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M 0 1.5 L 8 5 L 0 8.5 z" fill="#334155" />
    </marker>
  </defs>

  <!-- Background -->
  <rect width="1520" height="1340" class="diagram-bg" />

  <!-- Title Banner -->
  <g id="TitleBanner">
    <rect x="35" y="25" width="1450" height="70" fill="#FFFFFF" stroke="#E2E8F0" stroke-width="1.5" rx="8" ry="8" />
    <text x="60" y="52" class="header-title">CodeQuery System Architecture &#8212; UML Activity Diagram</text>
    <text x="60" y="74" class="header-subtitle">Control &amp; Data Flow across System Partitions: Repository Ingestion, AST Code Parsing, Vector Chunking &amp; RAG Querying</text>
    
    <rect x="1340" y="44" width="125" height="28" fill="#F1F5F9" stroke="#CBD5E1" stroke-width="1" rx="14" ry="14" />
    <circle cx="1358" cy="58" r="4.5" fill="#10B981" />
    <text x="1370" y="62" font-family="'Segoe UI', Arial" font-size="11" font-weight="600" fill="#334155">UML 2.5</text>
  </g>

  <!-- ========================================================================= -->
  <!-- SWIMLANES / PARTITIONS                                                    -->
  <!-- ========================================================================= -->
  <!-- Lane 1: Client & API Layer (width: 320, x: 35 to 355) -->
  <rect x="35" y="115" width="320" height="1150" class="lane-bg-1" />
  <rect x="35" y="115" width="320" height="48" class="lane-header-1" />
  <text x="195" y="136" class="lane-title">Client &amp; API Gateway</text>
  <text x="195" y="151" class="lane-sub">FastAPI Routes &amp; HTTP Controllers</text>

  <!-- Lane 2: Repository & CodeParser (width: 380, x: 355 to 735) -->
  <rect x="355" y="115" width="380" height="1150" class="lane-bg-2" />
  <rect x="355" y="115" width="380" height="48" class="lane-header-2" />
  <text x="545" y="136" class="lane-title">Repository &amp; AST Parser</text>
  <text x="545" y="151" class="lane-sub">RepositoryService &amp; CodeParser</text>

  <!-- Lane 3: Segmentation & Vector Indexing (width: 400, x: 735 to 1135) -->
  <rect x="735" y="115" width="400" height="1150" class="lane-bg-3" />
  <rect x="735" y="115" width="400" height="48" class="lane-header-3" />
  <text x="935" y="136" class="lane-title">Segmentation &amp; Storage</text>
  <text x="935" y="151" class="lane-sub-green">CodeChunker, FastEmbed &amp; ChromaDB</text>

  <!-- Lane 4: Query Engine & Local LLM (width: 350, x: 1135 to 1485) -->
  <rect x="1135" y="115" width="350" height="1150" class="lane-bg-4" />
  <rect x="1135" y="115" width="350" height="48" class="lane-header-4" />
  <text x="1310" y="136" class="lane-title">Query Engine &amp; LLM</text>
  <text x="1310" y="151" class="lane-sub-amber">QueryService &amp; Ollama Qwen 1.5B</text>

  <!-- ========================================================================= -->
  <!-- LANE 1: INITIAL DISPATCH & WORKFLOW BRANCHING                             -->
  <!-- ========================================================================= -->
  <!-- Start Node -->
  <circle cx="195" cy="190" r="13" fill="#1E293B" stroke="#0F172A" stroke-width="2" />
  
  <!-- Flow: Start -> Receive Request -->
  <line x1="195" y1="203" x2="195" y2="224" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="191,222 199,222 195,228" fill="#334155" />

  <!-- Action: Receive Request -->
  <rect x="85" y="228" width="220" height="44" class="act-node" />
  <text x="195" y="247" class="act-title">Receive HTTP Request</text>
  <text x="195" y="261" class="act-detail">/analyze-repository or /query</text>

  <!-- Flow -> Decision 1 -->
  <line x1="195" y1="272" x2="195" y2="295" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="191,293 199,293 195,299" fill="#334155" />

  <!-- Decision 1: Request Type -->
  <polygon points="195,299 225,317 195,335 165,317" class="decision-node" />
  <text x="195" y="320" class="decision-label">Route?</text>

  <!-- Flow 1A: [Analyze Repo] -> Lane 2 -->
  <path d="M 225 317 L 435 317" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="429,313 429,321 437,317" fill="#334155" />
  <text x="235" y="310" class="guard-text">[POST /analyze-repository]</text>

  <!-- Flow 1B: [Query] -> Lane 4 (Path across top) -->
  <path d="M 195 335 L 195 365 L 1310 365 L 1310 395" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1306,393 1314,393 1310,399" fill="#334155" />
  <text x="205" y="358" class="guard-text-amber">[POST /query]</text>


  <!-- ========================================================================= -->
  <!-- LANE 2: REPOSITORY INGESTION & AST PARSING PIPELINE                       -->
  <!-- ========================================================================= -->
  <!-- Action: Extract Repo URL -->
  <rect x="437" y="295" width="215" height="44" class="act-node-purple" />
  <text x="545" y="314" class="act-title">Parse Repository Request</text>
  <text x="545" y="328" class="act-detail">Extract repo name &amp; target path</text>

  <!-- Flow -> Decision 2: Cached? -->
  <line x1="545" y1="339" x2="545" y2="368" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="541,366 549,366 545,372" fill="#334155" />

  <!-- Decision 2: Cache check -->
  <polygon points="545,372 585,392 545,412 505,392" class="decision-node" />
  <text x="545" y="395" class="decision-label">Cached?</text>

  <!-- Branch 2A: [Yes, Valid] -> Reuse -->
  <path d="M 505 392 L 440 392 L 440 435" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="436,433 444,433 440,439" fill="#334155" />
  <text x="445" y="385" class="guard-text">[Valid Repo]</text>
  
  <rect x="375" y="439" width="130" height="42" class="act-node-purple" />
  <text x="440" y="457" class="act-title">Reuse Repo</text>
  <text x="440" y="470" class="act-detail">Verify not bare</text>

  <!-- Branch 2B: [No / Corrupt] -> Git Clone -->
  <path d="M 585 392 L 650 392 L 650 435" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="646,433 654,433 650,439" fill="#334155" />
  <text x="590" y="385" class="guard-text-amber">[Missing/Corrupt]</text>

  <rect x="580" y="439" width="140" height="42" class="act-node-purple" />
  <text x="650" y="457" class="act-title">Git Shallow Clone</text>
  <text x="650" y="470" class="act-detail">depth=1, single_branch</text>

  <!-- Merge 2 -->
  <path d="M 440 481 L 440 505 L 530 505" class="flow-line" />
  <path d="M 650 481 L 650 505 L 560 505" class="flow-line" />
  <polygon points="545,497 560,505 545,513 530,505" class="decision-node" />

  <!-- Flow -> Scan Repo -->
  <line x1="545" y1="513" x2="545" y2="534" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="541,532 549,532 545,538" fill="#334155" />

  <!-- Action: Scan Directory Tree -->
  <rect x="437" y="538" width="215" height="44" class="act-node-purple" />
  <text x="545" y="557" class="act-title">Scan Directory Tree</text>
  <text x="545" y="571" class="act-detail">os.walk() identifying .py files</text>

  <!-- Flow -> Filter Excluded -->
  <line x1="545" y1="582" x2="545" y2="604" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="541,602 549,602 545,608" fill="#334155" />

  <!-- Action: Filter Excluded Dirs -->
  <rect x="437" y="608" width="215" height="44" class="act-node-purple" />
  <text x="545" y="627" class="act-title">Filter Excluded Directories</text>
  <text x="545" y="641" class="act-detail">Prune .git, venv, tests, docs</text>

  <!-- Flow -> Parse Python Files (AST) -->
  <line x1="545" y1="652" x2="545" y2="674" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="541,672 549,672 545,678" fill="#334155" />

  <!-- Action: Parse Python Files with AST -->
  <rect x="437" y="678" width="215" height="44" class="act-node-purple" />
  <text x="545" y="697" class="act-title">Parse Python AST (ast.parse)</text>
  <text x="545" y="711" class="act-detail">Generate abstract syntax tree</text>

  <!-- Flow -> Extract Structural Info -->
  <line x1="545" y1="722" x2="545" y2="744" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="541,742 549,742 545,748" fill="#334155" />

  <!-- Action: Extract Structural Info -->
  <rect x="437" y="748" width="215" height="44" class="act-node-purple" />
  <text x="545" y="767" class="act-title">Extract AST Structural Nodes</text>
  <text x="545" y="781" class="act-detail">Classes, methods, calls &amp; imports</text>

  <!-- Flow Lane 2 -> Lane 3 -->
  <path d="M 652 770 L 825 770" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="819,766 819,774 827,770" fill="#334155" />
  <text x="670" y="763" class="guard-text">parsed_files</text>


  <!-- ========================================================================= -->
  <!-- LANE 3: CHUNKING, EMBEDDING & CHROMADB STORAGE PIPELINE                   -->
  <!-- ========================================================================= -->
  <!-- Action: Create Code Chunks -->
  <rect x="827" y="748" width="215" height="44" class="act-node-emerald" />
  <text x="935" y="767" class="act-title">Segment into Code Chunks</text>
  <text x="935" y="781" class="act-detail">create_code_chunks(parsed_file)</text>

  <!-- Flow -> Decision 3: Size > 1500? -->
  <line x1="935" y1="792" x2="935" y2="817" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="931,815 939,815 935,821" fill="#334155" />

  <!-- Decision 3: Size check -->
  <polygon points="935,821 975,841 935,861 895,841" class="decision-node" />
  <text x="935" y="844" class="decision-label">&gt; 1500?</text>

  <!-- Branch 3A: [Yes] -> Split Large Chunk -->
  <path d="M 895 841 L 820 841 L 820 882" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="816,880 824,880 820,886" fill="#334155" />
  <text x="828" y="834" class="guard-text-amber">[&gt; 1500 chars]</text>

  <rect x="755" y="886" width="130" height="42" class="act-node-emerald" />
  <text x="820" y="904" class="act-title">Split Large Chunk</text>
  <text x="820" y="917" class="act-detail">Line boundaries</text>

  <!-- Branch 3B: [No] -> Keep intact -->
  <path d="M 975 841 L 1050 841 L 1050 882" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1046,880 1054,880 1050,886" fill="#334155" />
  <text x="985" y="834" class="guard-text">[&lt;= 1500 chars]</text>

  <rect x="985" y="886" width="130" height="42" class="act-node-emerald" />
  <text x="1050" y="904" class="act-title">Retain Unit Chunk</text>
  <text x="1050" y="917" class="act-detail">Original size</text>

  <!-- Merge 3 -->
  <path d="M 820 928 L 820 950 L 920 950" class="flow-line" />
  <path d="M 1050 928 L 1050 950 L 950 950" class="flow-line" />
  <polygon points="935,942 950,950 935,958 920,950" class="decision-node" />

  <!-- Flow -> Filter tiny chunks -->
  <line x1="935" y1="958" x2="935" y2="978" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="931,976 939,976 935,982" fill="#334155" />

  <!-- Action: Filter Chunks < 100 -->
  <rect x="827" y="982" width="215" height="40" class="act-node-emerald" />
  <text x="935" y="999" class="act-title">Filter Chunks &lt; 100 Characters</text>
  <text x="935" y="1013" class="act-detail">Eliminates noise &amp; trivial lines</text>

  <!-- Flow -> Fork Bar -->
  <line x1="935" y1="1022" x2="935" y2="1042" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="931,1040 939,1040 935,1046" fill="#334155" />

  <!-- FORK BAR (PARALLEL PREPARATION) -->
  <rect x="785" y="1046" width="300" height="7" class="sync-bar" />
  <text x="935" y="1040" class="sync-label" text-anchor="middle">FORK: PARALLEL PREPARATION</text>

  <!-- Branch Fork 1: Prepare Canonical Chunk IDs & Metadatas -->
  <path d="M 845 1053 L 845 1072" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="841,1070 849,1070 845,1076" fill="#334155" />

  <rect x="760" y="1076" width="170" height="42" class="act-node-emerald" />
  <text x="845" y="1094" class="act-title">Format Canonical IDs</text>
  <text x="845" y="1107" class="act-detail">{repo}::{path}::{type}::{line}</text>

  <!-- Branch Fork 2: FastEmbed Generation -->
  <path d="M 1025 1053 L 1025 1072" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1021,1070 1029,1070 1025,1076" fill="#334155" />

  <rect x="940" y="1076" width="170" height="42" class="act-node-emerald" />
  <text x="1025" y="1094" class="act-title">FastEmbed Vectors</text>
  <text x="1025" y="1107" class="act-detail">BAAI-384 + Cache lookup</text>

  <!-- JOIN BAR -->
  <path d="M 845 1118 L 845 1137" class="flow-line" />
  <path d="M 1025 1118 L 1025 1137" class="flow-line" />
  <rect x="785" y="1137" width="300" height="7" class="sync-bar" />
  <text x="935" y="1155" class="sync-label" text-anchor="middle">JOIN: SYNCHRONIZED STORAGE</text>

  <!-- Flow -> Batch Upsert ChromaDB -->
  <line x1="935" y1="1144" x2="935" y2="1164" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="931,1162 939,1162 935,1168" fill="#334155" />

  <!-- Action: Batch Upsert ChromaDB -->
  <rect x="827" y="1168" width="215" height="44" class="act-node-emerald" />
  <text x="935" y="1187" class="act-title">Batch Upsert ChromaDB</text>
  <text x="935" y="1201" class="act-detail">collection.upsert(batch=500)</text>

  <!-- Flow -> Back to Lane 1 -->
  <path d="M 827 1190 L 307 1190" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="313,1186 313,1194 305,1190" fill="#334155" />
  <text x="560" y="1183" class="guard-text">indexing_summary</text>

  <!-- Lane 1 Action: Return Ingestion Response -->
  <rect x="85" y="1168" width="220" height="44" class="act-node" />
  <text x="195" y="1187" class="act-title">Return Ingestion Summary</text>
  <text x="195" y="1201" class="act-detail">HTTP 200 { status: "success" }</text>

  <!-- Flow -> Final Node 1 -->
  <line x1="195" y1="1212" x2="195" y2="1232" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="191,1230 199,1230 195,1236" fill="#334155" />

  <!-- Final Node 1 -->
  <circle cx="195" cy="1245" r="11" fill="#FFFFFF" stroke="#0F172A" stroke-width="2" />
  <circle cx="195" cy="1245" r="6" fill="#0F172A" />
  <text x="195" y="1268" font-family="'Segoe UI', Arial" font-size="9.5" font-weight="700" fill="#475569" text-anchor="middle">INGESTION COMPLETE</text>


  <!-- ========================================================================= -->
  <!-- LANE 4: SEMANTIC QUERY & RAG PIPELINE                                     -->
  <!-- ========================================================================= -->
  <!-- Action: Receive Question -->
  <rect x="1200" y="399" width="220" height="44" class="act-node-amber" />
  <text x="1310" y="418" class="act-title">Receive Code Question</text>
  <text x="1310" y="432" class="act-detail">QueryRequest(question, code)</text>

  <!-- Flow -> Generate Query Vector -->
  <line x1="1310" y1="443" x2="1310" y2="467" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1306,465 1314,465 1310,471" fill="#334155" />

  <!-- Action: Generate Question Embedding -->
  <rect x="1200" y="471" width="220" height="44" class="act-node-amber" />
  <text x="1310" y="490" class="act-title">Embed Question Vector</text>
  <text x="1310" y="504" class="act-detail">FastEmbed generate_embedding()</text>

  <!-- Flow -> Search ChromaDB -->
  <line x1="1310" y1="515" x2="1310" y2="539" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1306,537 1314,537 1310,543" fill="#334155" />

  <!-- Action: Search VectorStore -->
  <rect x="1200" y="543" width="220" height="44" class="act-node-amber" />
  <text x="1310" y="562" class="act-title">Search VectorStore (ChromaDB)</text>
  <text x="1310" y="576" class="act-detail">collection.query(n_results=3)</text>

  <!-- Flow -> Decision 4: Relevant Chunks Found? -->
  <line x1="1310" y1="587" x2="1310" y2="612" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1306,610 1314,610 1310,616" fill="#334155" />

  <!-- Decision 4: Chunks Found? -->
  <polygon points="1310,616 1350,636 1310,656 1270,636" class="decision-node" />
  <text x="1310" y="639" class="decision-label">Hits &gt; 0?</text>

  <!-- Branch 4A: [No Hits] -> Fallback -->
  <path d="M 1270 636 L 1185 636 L 1185 677" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1181,675 1189,675 1185,681" fill="#334155" />
  <text x="1195" y="629" class="guard-text-amber">[No Chunks]</text>

  <rect x="1145" y="681" width="130" height="42" class="act-node-amber" />
  <text x="1210" y="699" class="act-title">Fallback Message</text>
  <text x="1210" y="712" class="act-detail">"No relevant code"</text>

  <!-- Branch 4B: [Hits Found] -> Combine Context -->
  <path d="M 1350 636 L 1405 636 L 1405 677" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1401,675 1409,675 1405,681" fill="#334155" />
  <text x="1355" y="629" class="guard-text">[Hits &gt; 0]</text>

  <rect x="1335" y="681" width="140" height="42" class="act-node-amber" />
  <text x="1405" y="699" class="act-title">Assemble Context</text>
  <text x="1405" y="712" class="act-detail">Combine top-3 chunks</text>

  <!-- Flow -> Format Prompt -->
  <line x1="1405" y1="723" x2="1405" y2="748" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1401,746 1409,746 1405,752" fill="#334155" />

  <!-- Action: Format Prompt -->
  <rect x="1335" y="752" width="140" height="42" class="act-node-amber" />
  <text x="1405" y="770" class="act-title">Construct RAG Prompt</text>
  <text x="1405" y="783" class="act-detail">Code context + question</text>

  <!-- Flow -> Call Ollama LLM -->
  <line x1="1405" y1="794" x2="1405" y2="818" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1401,816 1409,816 1405,822" fill="#334155" />

  <!-- Action: Call Ollama LLM -->
  <rect x="1335" y="822" width="140" height="44" class="act-node-amber" />
  <text x="1405" y="841" class="act-title">Query Local Ollama</text>
  <text x="1405" y="855" class="act-detail">qwen2.5-coder:1.5b</text>

  <!-- Merge 4 -->
  <path d="M 1210 723 L 1210 885 L 1295 885" class="flow-line" />
  <path d="M 1405 866 L 1405 885 L 1325 885" class="flow-line" />
  <polygon points="1310,877 1325,885 1310,893 1295,885" class="decision-node" />

  <!-- Flow -> Format Final Answer -->
  <line x1="1310" y1="893" x2="1310" y2="915" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="1306,913 1314,913 1310,919" fill="#334155" />

  <!-- Action: Format Final Answer -->
  <rect x="1200" y="919" width="220" height="42" class="act-node-amber" />
  <text x="1310" y="937" class="act-title">Extract &amp; Format Answer</text>
  <text x="1310" y="950" class="act-detail">Clean markdown explanation</text>

  <!-- Flow Lane 4 -> Lane 1 -->
  <path d="M 1200 940 L 307 940" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="313,936 313,944 305,940" fill="#334155" />
  <text x="730" y="933" class="guard-text-amber">return answer: str</text>

  <!-- Lane 1 Action: Return Query Response -->
  <rect x="85" y="919" width="220" height="42" class="act-node" />
  <text x="195" y="937" class="act-title">Return Query JSON Response</text>
  <text x="195" y="950" class="act-detail">HTTP 200 { question, answer }</text>

  <!-- Flow -> Final Node 2 -->
  <line x1="195" y1="961" x2="195" y2="985" class="flow-line" marker-end="url(#flow-arrow)" />
  <polygon points="191,983 199,983 195,989" fill="#334155" />

  <!-- Final Node 2 -->
  <circle cx="195" cy="998" r="11" fill="#FFFFFF" stroke="#0F172A" stroke-width="2" />
  <circle cx="195" cy="998" r="6" fill="#0F172A" />
  <text x="195" y="1021" font-family="'Segoe UI', Arial" font-size="9.5" font-weight="700" fill="#475569" text-anchor="middle">QUERY COMPLETE</text>

  <!-- ========================================================================= -->
  <!-- LEGEND                                                                    -->
  <!-- ========================================================================= -->
  <g id="Legend">
    <rect x="35" y="1285" width="1450" height="42" class="legend-box" />
    <text x="55" y="1311" class="legend-title">UML 2.5 ACTIVITY NOTATION:</text>
    
    <circle cx="255" cy="1306" r="8" fill="#1E293B" />
    <text x="270" y="1310" class="legend-text">Initial Node</text>

    <circle cx="370" cy="1306" r="8" fill="#FFFFFF" stroke="#0F172A" stroke-width="2" />
    <circle cx="370" cy="1306" r="4" fill="#0F172A" />
    <text x="385" y="1310" class="legend-text">Activity Final Node</text>

    <polygon points="505,1301 517,1306 505,1311 493,1306" class="decision-node" />
    <text x="525" y="1310" class="legend-text">Decision / Merge Node</text>

    <rect x="680" y="1303" width="30" height="6" class="sync-bar" />
    <text x="720" y="1310" class="legend-text">Fork / Join Synchronization Bar</text>

    <line x1="915" y1="1306" x2="955" y2="1306" class="flow-line" />
    <polygon points="951,1302 951,1310 959,1306" fill="#334155" />
    <text x="970" y="1310" class="legend-text">Control / Data Flow</text>

    <rect x="1130" y="1300" width="12" height="12" class="act-node" />
    <text x="1150" y="1310" class="legend-text">API Activity</text>

    <rect x="1235" y="1300" width="12" height="12" class="act-node-purple" />
    <text x="1255" y="1310" class="legend-text">Parser Activity</text>

    <rect x="1355" y="1300" width="12" height="12" class="act-node-emerald" />
    <text x="1375" y="1310" class="legend-text">Embedding / DB</text>
  </g>

</svg>
'''
    output_path = r"c:\Users\LENOVO\codequery\codequery_activity_diagram.svg"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    ET.fromstring(svg)
    print(f"Validated XML: successfully generated {output_path} ({len(svg)} bytes)")

if __name__ == "__main__":
    generate_activity_diagram()
