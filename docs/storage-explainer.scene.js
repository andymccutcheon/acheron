// ===== SCENE START =====
const THEME = "pattern";
// Preserve tool identifiers and the engine name after theme sentence casing.
for (const key of ["titleCase", "pillFmt", "labelFmt"]) {
  const format = TH[key];
  TH[key] = value => format(value)
    .replace(/\bcontext_search\b/gi, "context_search")
    .replace(/\bbuild_context\b/gi, "build_context")
    .replace(/\bbasic memory\b/gi, "Basic Memory");
}
const SCENE={
  title:"How files become a knowledge graph",
  code:"EXPLAINER 04", kicker:"STORAGE // RELATIONS",
  note:"Traced file: concepts/Sync Engine.md. Outgoing wikilinks shown as graph edges.",
  crosshairs:[],
  legend:[["REQUEST",C.request],["RESULT / DATA",C.data],["ACTIVE",C.active],["FAILED",C.fail]],
  introTitle:"One note, from file to graph",
  introText:"Ten steps through the storage layer for the Tidepool demo corpus. Step with the arrow keys or use the playback controls.",
};
const FOLDERS=["concepts · 5","decisions · 6","guides · 3","incidents · 3","meetings · 3","people · 3"];
const SCENARIOS=[{label:"Sync Engine joins the graph",
  file:"Sync Engine.md",
  index:["watcher · sees new file","parser · frontmatter + links","index · SQLite · hybrid search","permalink · stable address"],
  nodes:["Conflict Resolution","Storage Layer","2025-11 Sync storm"],
  read:["find · similarity search","walk · links & backlinks","answer · page + neighborhood"],
}];
const R={};
function edgePath(d,color){ const p=el("path",{d,fill:"none",stroke:color,"stroke-width":1.5,"stroke-linecap":"round",opacity:0},par("graph"));
  onReset(()=>p.setAttribute("opacity",0)); return p; }
function buildScene(){
  panel("vault",{x:40,y:96,w:300,h:320,code:"V-01",title:"demo library",chip:"CANONICAL"});
  text("vault",56,140,"plain markdown · watched folders","body2",{maxW:230});
  R.corp=[0,1,2].map(i=>slot("vault",56,156+i*24,268,22));
  R.corp2=[0,1,2].map(i=>slot("vault",56,234+i*24,268,22));
  R.file=slot("vault",56,312,268,28);

  panel("index",{x:400,y:96,w:300,h:304,code:"I-01",title:"THE INDEX",chip:"STANDBY"});
  text("index",416,140,"Basic Memory · local service","body2",{maxW:240});
  R.stage=[0,1,2,3].map(i=>slot("index",416,162+i*36,268,26));
  R.idx=dynText("index",416,336,"body2",{maxW:250});

  panel("graph",{x:760,y:96,w:480,h:304,code:"G-01",title:"THE GRAPH",chip:"DERIVED"});
  R.eCr=edgePath("M920,189 C940,189 940,239 960,239",C.data);
  R.eSt=edgePath("M850,202 L850,286",C.lineHi);
  R.eStorm=edgePath("M1125,286 L1125,254",C.data);
  R.nd1=slot("graph",780,176,140,26);
  R.nd2=slot("graph",1030,150,190,26);
  R.nd3=slot("graph",1030,286,190,26);
  R.nd0=slot("graph",960,224,180,30);
  R.walk=dynText("graph",776,368,"body2",{maxW:300});

  panel("surface",{x:40,y:446,w:560,h:144,code:"M-01",title:"ONE SURFACE",chip:"MCP"});
  text("surface",56,486,"one server · every tool","body2",{maxW:300});
  R.p1=pill("surface",56,502,250,"context_search · ranked");
  R.p2=pill("surface",56,532,250,"build_context · graph walk");
  R.p3=pill("surface",56,562,250,"engine tools · proxied");

  panel("read",{x:640,y:446,w:600,h:144,code:"R-01",title:"THE READ",chip:"TWO PATHS"});
  text("read",656,486,"two ways over one index","body2",{maxW:300});
  R.read=[0,1,2].map(i=>slot("read",656,502+i*30,568,26));

  wire("w-file","M340,300 C372,300 368,211 400,211");
  wire("e-cr","M920,189 C940,189 940,239 960,239",{both:true});
  wire("e-st","M850,202 L850,286",{both:true});
  wire("e-storm","M1125,286 L1125,254",{both:true});
  wire("w-find","M260,446 C360,425 460,406 550,400",{both:true});
  wire("w-walk","M420,446 C600,442 720,404 820,400",{both:true});
}
const STEPS=[
 {t:"Plain files, one library", d:3.8, x:()=>"Twenty-three notes in six folders make up the Tidepool demo library. The database is only an index over these markdown files.",
  a:p=>{ setActive("vault");
    FOLDERS.forEach((t,i)=>{
      const s=i<3?R.corp[i]:R.corp2[i-3];
      s.show(t,C.lineHi,sub(p,.06+i*.1,.32+i*.1));
    });
    R.nd1.show(S.nodes[0],C.lineHi,sub(p,.45,.65)); R.nd2.show(S.nodes[1],C.lineHi,sub(p,.5,.7));
    R.nd3.show(S.nodes[2],C.lineHi,sub(p,.55,.75)); }},
 {t:"A note on disk", d:3.4, x:()=>"Writing a file is the whole write path. This scene traces concepts/Sync Engine.md from the demo corpus.",
  a:p=>{ setActive("vault"); R.file.show(S.file,C.request,sub(p,.15,.75)); }},
 {t:"The watcher queues it", d:3.2, x:()=>"The file watcher picks up changes and queues indexing. Save a note and your agent can find it in under a minute.",
  a:p=>{ setActive("index"); setChip("index","WATCHING","idle");
    packet(0,[["w-file",0]],sub(p,.2,.8),"req","new note","below");
    R.stage[0].show(S.index[0],C.request,sub(p,.35,.6)); }},
 {t:"Parsed into an entity", d:3.8, x:()=>"The parser reads frontmatter, tags, and wikilinks. The note gets a stable permalink in the local SQLite index.",
  a:p=>{ setActive("index");
    R.stage[0].show(S.index[0],C.data,1);
    R.stage[1].show(S.index[1],C.data,sub(p,.1,.4));
    R.stage[2].show(S.index[2],C.data,sub(p,.3,.6));
    R.stage[3].show(S.index[3],C.data,sub(p,.5,.8));
    R.file.show(S.file,C.data,1);
    R.idx.set(p>.75?"indexed · under a minute":"",C.ink2);
    if(p>.8) setChip("index","INDEXED","done"); }},
 {t:"Links become edges", d:4.2, x:()=>"Each [[wikilink]] in Sync Engine.md resolves to a relation. Three outgoing links shown here: Conflict Resolution, Storage Layer, and 2025-11 Sync storm.",
  a:p=>{ setActive("graph");
    R.nd0.show("Sync Engine",p<.25?C.request:C.data,sub(p,.08,.28));
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,sub(p,.2,.35)); R.nd3.show(S.nodes[2],C.data,sub(p,.25,.4));
    packet(0,[["e-cr",0]],sub(p,.25,.5),"req");
    packet(1,[["e-st",0]],sub(p,.45,.7),"req");
    packet(2,[["e-storm",0]],sub(p,.7,1),"req");
    if(p>=.5) R.eCr.setAttribute("opacity",.9);
    if(p>=.7) R.eSt.setAttribute("opacity",.9);
    if(p>=1){ R.eStorm.setAttribute("opacity",.9); setChip("graph","LINKED","done"); } }},
 {t:"A graph you can walk", d:3.6, x:()=>"Proxied tools such as build_context return a note plus its neighborhood. One hop is enough to see related decisions and incidents.",
  a:p=>{ setActive("graph");
    R.nd0.show("Sync Engine",C.data,1);
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,1); R.nd3.show(S.nodes[2],C.data,1);
    R.walk.set(p>.3?"outgoing links · depth 1":"",C.data);
    packet(3,[["e-cr",1]],sub(p,.35,.85),"res","1 hop"); }},
 {t:"The index is disposable", d:4.0, x:()=>"Delete the SQLite index and rebuild from files. Markdown stays canonical; the graph stays derived.",
  a:p=>{ setActive("index");
    const drop=p<.45;
    R.stage.forEach((s,i)=>s.show(S.index[i],drop?C.dim:C.data,1));
    R.file.show(S.file,drop?C.request:C.data,1);
    R.idx.set(drop?"index.sqlite removed":"rebuilt from files",drop?C.request:C.data);
    if(p<.5) setChip("index","REBUILDING","idle"); else setChip("index","REBUILT","done"); }},
 {t:"One MCP surface", d:3.6, x:()=>"One MCP server fronts ranked search, graph walks, and every engine tool discovered at startup.",
  a:p=>{ setActive("surface");
    R.p1.set(p>=.25?"ok":p>=.05?"active":null);
    R.p2.set(p>=.5?"ok":p>=.3?"active":null);
    R.p3.set(p>=.75?"ok":p>=.55?"active":null);
    if(p>=1) setChip("surface","OPEN","done"); }},
 {t:"Two read paths", d:4.0, x:()=>"context_search reads by similarity; build_context walks links. Both hit the same index underneath.",
  a:p=>{ R.p1.set("ok"); R.p2.set("ok"); R.p3.set("ok");
    packet(0,[["w-find",0]],sub(p,.05,.4),"req","find");
    R.read[0].show(S.read[0],C.data,sub(p,.15,.4));
    packet(1,[["w-walk",0]],sub(p,.4,.75),"req","walk");
    R.read[1].show(S.read[1],C.data,sub(p,.5,.75));
    R.read[2].show(S.read[2],C.data,sub(p,.8,.95));
    if(p>=.95){ setChip("read","ANSWERED","done"); setActive("read"); } else setActive("surface"); }},
 {t:"Files in, knowledge out", d:3.8, x:()=>"The demo library compounds one markdown file at a time: searchable, linked, and current for agents.",
  a:p=>{ setActive("vault");
    FOLDERS.forEach((t,i)=>{
      const s=i<3?R.corp[i]:R.corp2[i-3];
      s.show(t,C.data,sub(p,.04+i*.08,.28+i*.08));
    });
    R.file.show(S.file,C.data,1);
    R.nd0.show("Sync Engine",C.data,1);
    R.nd1.show(S.nodes[0],C.data,1); R.nd2.show(S.nodes[1],C.data,1); R.nd3.show(S.nodes[2],C.data,1);
    R.walk.set("searchable · linked · current",C.data);
    R.read.forEach((s,i)=>s.show(S.read[i],C.data,1));
    R.stage.forEach((s,i)=>s.show(S.index[i],C.data,1));
    R.p1.set("ok"); R.p2.set("ok"); R.p3.set("ok"); }},
];
function afterRender(k){ /* derived displays: none */ }
// ===== SCENE END =====
