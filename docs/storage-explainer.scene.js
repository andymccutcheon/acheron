/* Visual explainer scene: the storage layer — markdown source of truth, local index, relations graph.
   Evidence (live traversals, 2026-10-05): concepts/Memory → note, maps/Orchestration → note, people/@omarsar0 → note. */
// ===== SCENE START =====
const THEME = "product-dark";
const SCENE={
  title:"How files become a knowledge graph",
  code:"EXPLAINER 04", kicker:"STORAGE // RELATIONS",
  note:"The traced note and its three inbound links are real entries in the vault.",
  crosshairs:[],
  legend:[["REQUEST",C.request],["RESULT / DATA",C.data],["ACTIVE / FAILED",C.active],["STANDBY",C.dim]],
  introTitle:"One note, from file to graph",
  introText:"Ten steps through the storage layer — markdown in, a local index, and the links that turn it into a graph. Press play, or step through with the arrow keys.",
};
const SCENARIOS=[{label:"A note joins the graph",
  file:"Building Faster Memory.md",
  corpora:["bookmarks · 409 notes","agent memory · 10 notes","briefs · 8 notes"],
  index:["watcher · sees new file","parser · frontmatter + links","index · SQLite · hybrid search","permalink · stable address"],
  nodes:["Memory · concept","@omarsar0 · author","Orchestration · map","Best Stack · note"],
  read:["find · similarity search","walk · links & backlinks","answer · page + its neighborhood"],
}];
const R={};
function edgePath(d,color){ const p=el("path",{d,fill:"none",stroke:color,"stroke-width":1.5,"stroke-linecap":"round",opacity:0},par("graph"));
  onReset(()=>p.setAttribute("opacity",0)); return p; }
function buildScene(){
  // Vault — the files themselves.
  panel("vault",{x:40,y:96,w:300,h:304,code:"V-01",title:"THE VAULT",chip:"CANONICAL"});
  text("vault",56,140,"plain markdown · watched folders","body2",{maxW:230});
  R.corp=[0,1,2].map(i=>slot("vault",56,156+i*36,268,26));
  R.file=slot("vault",56,286,268,30);

  // Index — the local service that derives from the files.
  panel("index",{x:400,y:96,w:300,h:304,code:"I-01",title:"THE INDEX",chip:"STANDBY"});
  text("index",416,140,"Basic Memory · local service","body2",{maxW:240});
  R.stage=[0,1,2,3].map(i=>slot("index",416,162+i*36,268,26));
  R.idx=dynText("index",416,336,"body2",{maxW:250});

  // Graph — nodes are entities, edges are indexed links.
  panel("graph",{x:760,y:96,w:480,h:304,code:"G-01",title:"THE GRAPH",chip:"DERIVED"});
  R.eBest=edgePath("M850,202 L850,286",C.lineHi);
  R.eMem=edgePath("M920,189 C940,189 940,239 960,239",C.data);
  R.eAuth=edgePath("M1125,176 L1125,224",C.data);
  R.eOrch=edgePath("M1125,286 L1125,254",C.data);
  R.nd1=slot("graph",780,176,140,26);
  R.nd4=slot("graph",780,286,140,26);
  R.nd2=slot("graph",1030,150,190,26);
  R.nd3=slot("graph",1030,286,190,26);
  R.nd0=slot("graph",960,224,180,30);
  R.walk=dynText("graph",776,368,"body2",{maxW:300});

  // One surface — the single MCP door.
  panel("surface",{x:40,y:446,w:560,h:144,code:"M-01",title:"ONE SURFACE",chip:"MCP"});
  text("surface",56,486,"one server · every tool","body2",{maxW:300});
  R.p1=pill("surface",56,502,250,"context_search · ranked");
  R.p2=pill("surface",56,532,250,"build_context · graph walk");
  R.p3=pill("surface",56,562,250,"+ 23 more tools · proxied");

  // The read — two views over the same index.
  panel("read",{x:640,y:446,w:600,h:144,code:"R-01",title:"THE READ",chip:"TWO PATHS"});
  text("read",656,486,"two ways over one index","body2",{maxW:300});
  R.read=[0,1,2].map(i=>slot("read",656,502+i*30,568,26));

  // Wires: file → index; existing graph edges; surface → index and graph.
  wire("w-file","M340,300 C372,300 368,211 400,211");
  wire("e-mem","M920,189 C940,189 940,239 960,239",{both:true});
  wire("e-auth","M1125,176 L1125,224",{both:true});
  wire("e-orch","M1125,286 L1125,254",{both:true});
  wire("e-best","M850,202 L850,286",{both:true});
  wire("w-find","M260,446 C360,425 460,406 550,400",{both:true});
  wire("w-walk","M420,446 C600,442 720,404 820,400",{both:true});
}
const STEPS=[
 {t:"Plain files, one source of truth", d:3.8, x:()=>"Three corpora — bookmarks, agent memory, project briefs — as plain markdown in watched folders. The database is only ever an index over these files.",
  a:p=>{ setActive("vault");
    R.eBest.setAttribute("opacity",.5);
    R.corp.forEach((s,i)=>s.show(S.corpora[i],C.lineHi,sub(p,.08+i*.16,.4+i*.16)));
    R.nd1.show(S.nodes[0],C.lineHi,sub(p,.5,.7)); R.nd2.show(S.nodes[1],C.lineHi,sub(p,.56,.76));
    R.nd3.show(S.nodes[2],C.lineHi,sub(p,.62,.82)); R.nd4.show(S.nodes[3],C.lineHi,sub(p,.68,.88)); }},
 {t:"A new note lands", d:3.4, x:()=>"A harvester writes a new note: one file lands in the vault. No import API and no migration — writing a file is the entire write path.",
  a:p=>{ setActive("vault"); R.file.show(S.file,C.request,sub(p,.15,.75)); }},
 {t:"The watcher notices", d:3.2, x:()=>"The file watcher notices within about twenty seconds and queues the note for indexing.",
  a:p=>{ setActive("index"); setChip("index","WATCHING","idle");
    packet(0,[["w-file",0]],sub(p,.2,.8),"req","new note","below");
    R.stage[0].show(S.index[0],C.active,sub(p,.35,.6)); }},
 {t:"Parsed into an entity", d:3.8, x:()=>"The parser reads frontmatter, tags and links; the note becomes an entity with a stable permalink in the local SQLite index.",
  a:p=>{ setActive("index");
    R.stage[0].show(S.index[0],C.data,1);
    R.stage[1].show(S.index[1],C.data,sub(p,.1,.4));
    R.stage[2].show(S.index[2],C.data,sub(p,.3,.6));
    R.stage[3].show(S.index[3],C.data,sub(p,.5,.8));
    R.file.show(S.file,C.data,1);
    R.idx.set(p>.75?"indexed in ~20 s":"",C.ink2);
    if(p>.8) setChip("index","INDEXED","done"); }},
 {t:"Links become edges", d:4.2, x:()=>"Each wikilink resolves into a typed relation. This note is already referenced by three pages: a concept, an author page and a map.",
  a:p=>{ setActive("graph");
    R.nd0.show("faster memory · note",p<.25?C.request:C.data,sub(p,.08,.28));
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,sub(p,.2,.35)); R.nd3.show(S.nodes[2],C.data,sub(p,.25,.4));
    packet(0,[["e-mem",0]],sub(p,.25,.5),"req");
    packet(1,[["e-auth",0]],sub(p,.5,.75),"req");
    packet(2,[["e-orch",0]],sub(p,.75,1),"req");
    if(p>=.5) R.eMem.setAttribute("opacity",.9);
    if(p>=.75) R.eAuth.setAttribute("opacity",.9);
    if(p>=1){ R.eOrch.setAttribute("opacity",.9); setChip("graph","LINKED","done"); } }},
 {t:"A graph you can walk", d:3.6, x:()=>"What you get is a graph you can walk. One hop returns a note's neighborhood — the context around it, not just the page.",
  a:p=>{ setActive("graph");
    R.nd0.show("faster memory · note",C.data,1);
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,1); R.nd3.show(S.nodes[2],C.data,1);
    R.walk.set(p>.3?"backlinks · 3 pages · depth 1":"",C.data);
    packet(3,[["e-mem",1]],sub(p,.35,.85),"res","1 hop"); }},
 {t:"The index is disposable", d:4.0, x:()=>"Delete the index and nothing is lost: it rebuilds from the files. Markdown stays canonical, the graph stays derived.",
  a:p=>{ setActive("index");
    const drop=p<.45;
    R.stage.forEach((s,i)=>s.show(S.index[i],drop?C.dim:C.data,1));
    R.file.show(S.file,drop?C.request:C.data,1);
    R.idx.set(drop?"index.sqlite removed":"rebuilt from files",drop?C.active:C.data);
    if(p<.5) setChip("index","REBUILDING","idle"); else setChip("index","REBUILT","done"); }},
 {t:"One surface for every agent", d:3.6, x:()=>"One MCP server fronts it all — ranked search, graph traversal, and every storage tool behind a single door.",
  a:p=>{ setActive("surface");
    R.p1.set(p>=.25?"ok":p>=.05?"active":null);
    R.p2.set(p>=.5?"ok":p>=.3?"active":null);
    R.p3.set(p>=.75?"ok":p>=.55?"active":null);
    if(p>=1) setChip("surface","OPEN","done"); }},
 {t:"A query reads both ways", d:4.0, x:()=>"A query can read both ways: similarity finds the page; traversal hands back its neighborhood. Two views over one index.",
  a:p=>{ R.p1.set("ok"); R.p2.set("ok"); R.p3.set("ok");
    packet(0,[["w-find",0]],sub(p,.05,.4),"req","find");
    R.read[0].show(S.read[0],C.data,sub(p,.15,.4));
    packet(1,[["w-walk",0]],sub(p,.4,.75),"req","walk");
    R.read[1].show(S.read[1],C.data,sub(p,.5,.75));
    R.read[2].show(S.read[2],C.data,sub(p,.8,.95));
    if(p>=.95){ setChip("read","ANSWERED","done"); setActive("read"); } else setActive("surface"); }},
 {t:"Files in, knowledge out", d:3.8, x:()=>"Write markdown anywhere and it becomes searchable, linked and current. The library compounds one file at a time.",
  a:p=>{ setActive("vault");
    R.corp.forEach((s,i)=>s.show(S.corpora[i],C.data,sub(p,.05+i*.12,.35+i*.12)));
    R.file.show(S.file,C.data,1);
    R.nd0.show("faster memory · note",C.data,1);
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,1); R.nd3.show(S.nodes[2],C.data,1); R.nd4.show(S.nodes[3],C.lineHi,1);
    R.walk.set("searchable · linked · current",C.data);
    R.read.forEach((s,i)=>s.show(S.read[i],C.data,1));
    R.stage.forEach((s,i)=>s.show(S.index[i],C.data,1));
    R.p1.set("ok"); R.p2.set("ok"); R.p3.set("ok"); }},
];
function afterRender(k){ /* derived displays: none */ }
// ===== SCENE END =====
