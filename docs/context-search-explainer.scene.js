/* Visual explainer scene: the context-search path — Basic Memory recall, decision-model reranking, fallback floor.
   Evidence: Acheron README + src/acheron/{server,bm,decisions,ranking}.py (2026-10-03). */
// ===== SCENE START =====
const THEME = "product-dark";
const SCENE={
  title:"How a question becomes a ranked answer",
  code:"EXPLAINER 03", kicker:"CONTEXT // SEARCH PATH",
  note:"Candidate scores are illustrative; ranking figures from the published benchmark.",
  crosshairs:[],
  legend:[["REQUEST",C.request],["RESULT / DATA",C.data],["ACTIVE / FAILED",C.active],["STANDBY",C.dim]],
  introTitle:"One query, traced through the context layer",
  introText:"Eleven steps from a question to a ranked answer — including what happens when the model is down. Press play, or step through with the arrow keys.",
};
const SCENARIOS=[
  {label:"Decision recall",
   query:["what did we decide","about sync conflicts?"],
   cands:["Hub / person page","CRDT decision","Sync engine notes","Sync storm incident"],
   scores:["0","3","3","1"],
   top:["CRDT decision","Sync engine notes","Sync storm incident","Hub / person page"],
   nativeTop:["Hub / person page","CRDT decision","Sync engine notes","Sync storm incident"],
   answer:["CRDT merge, chosen over","last-write-wins for the","offline notes corpus."]},
];
const PROJECTS=["bookmarks · 409","project notes · 10","briefs · 8"];
const R={};
function buildScene(){
  // Left column: the agent, its question, the answer it gets back.
  panel("agent",{x:40,y:110,w:230,h:170,code:"P-01",title:"AGENT",chip:"IDLE"});
  icon("agent","person",78,192,0.9);
  text("agent",112,158,"OpenCode","body2",{maxW:146});
  text("agent",112,180,"Claude Code","body2",{maxW:146});
  text("agent",112,202,"one MCP server","body2",{maxW:146});
  panel("ask",{x:40,y:300,w:360,h:120,title:null});
  R.ask=bubble("ask");
  panel("answer",{x:40,y:430,w:360,h:160,code:"R-01",title:"ANSWER",chip:"EMPTY"});
  R.ans=[0,1,2,3].map(i=>slot("answer",56,474+i*28,328,24));

  // Centre: the router, its candidate list.
  panel("router",{x:480,y:96,w:330,h:200,code:"M-01",title:"ACHERON",chip:"STANDBY"});
  R.rst=dynText("router",496,160,"body2",{maxW:298});
  R.cand=[0,1,2,3].map(i=>slot("router",496,176+i*28,298,24));

  // Right column: storage plane and decision model.
  panel("bm",{x:900,y:96,w:300,h:150,code:"S-01",title:"BASIC MEMORY",chip:"WATCHING"});
  icon("bm","db",1168,196,0.8);
  text("bm",916,150,"HTTP MCP · port 8765","body2",{maxW:230});
  text("bm",916,172,"hybrid search + SQLite","body2",{maxW:230});
  text("bm",916,194,"file watcher · ~20 s","body2",{maxW:230});
  panel("dec",{x:900,y:290,w:300,h:150,code:"S-02",title:"DECISION MODEL",chip:"STANDBY"});
  text("dec",916,344,"OpenRouter · Mercury Decide","body2",{maxW:268});
  text("dec",916,366,"free tier · 20 requests/min","body2",{maxW:268});
  R.scores=dynText("dec",916,392,"out",{maxW:268});

  // Bottom: the library that feeds the index.
  panel("lib",{x:480,y:470,w:720,h:120,code:"L-01",title:"THE LIBRARY · MARKDOWN NOTES",chip:"427 NOTES"});
  text("lib",496,508,"canonical files · watched folders","body2",{maxW:400});
  R.lib=PROJECTS.map((t,i)=>slot("lib",500+i*240,524,210,26));

  // Wires: agent <-> router, router <-> Basic Memory, router <-> model, library <-> Basic Memory.
  wire("a2r","M400,340 C440,340 440,150 480,150");
  wire("r2a","M480,210 C440,210 440,380 400,380");
  wire("r2b","M810,150 L900,150");
  wire("b2r","M900,200 L810,200");
  wire("r2d","M810,240 C860,240 860,340 900,340");
  wire("d2r","M900,390 C860,390 860,270 810,270");
  wire("bl","M700,470 C855,470 855,220 900,220",{both:true});
}
const STEPS=[
 {t:"The corpus, indexed", d:3.6, x:()=>"The corpus is plain markdown — a bookmark vault, agent memory, project briefs. Basic Memory keeps a local index over it, refreshed by a file watcher: no sync step, ever.",
  a:p=>{ setActive("lib");
    R.lib.forEach((s,i)=>s.show(PROJECTS[i],C.lineHi,sub(p,.1+i*.18,.4+i*.18)));
    setChip("bm","WATCHING","idle"); setChip("dec","STANDBY","standby"); setChip("router","STANDBY","standby");
    setChip("agent","IDLE","idle"); setChip("answer","EMPTY","idle"); }},
 {t:"A question arrives", d:3.4, x:()=>"OpenCode, Claude Code, any agent — one server for the whole library. Search comes back reranked; every other storage tool is proxied under its own name.",
  a:p=>{ R.ask.type(S.query,sub(p,0,.55),"QUERY",C.request);
    packet(0,[["a2r",0]],sub(p,.5,1),"req","context_search");
    if(p<.55) setActive("ask"); else setActive("router"); }},
 {t:"The router asks Basic Memory", d:3.4, x:()=>"An internal search_notes call to the long-running local service on port 8765. The index is warm and the loopback hop is cheap.",
  a:p=>{ R.rst.set("search_notes · 3 projects · top 10",C.ink2);
    packet(0,[["r2b",0]],sub(p,.15,.85),"req");
    setActive("router"); if(p>.7) setChip("bm","SEARCHING","idle"); }},
 {t:"Ten candidates return", d:3.6, x:()=>"Candidates come back across every project at once, straight from the engine's hybrid search.",
  a:p=>{ packet(0,[["b2r",0]],sub(p,0,.45),"res","10 NOTES");
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,sub(p,.35+i*.12,.6+i*.12)));
    if(p>.6){ setChip("bm","10 FOUND","done"); R.rst.set("10 candidates · 3 projects",C.ink2); setActive("router"); }
    else setActive("bm"); }},
 {t:"The model scores each candidate", d:3.6, x:()=>"Mercury Decide — a free System One model — scores each candidate 0 to 3 on usefulness. Scoring is its only job; no LLM writes the answer.",
  a:p=>{ R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,1));
    packet(0,[["r2d",0]],sub(p,.1,.75),"req","SCORE");
    setActive("dec"); R.scores.set("scoring 10 candidates");
    if(p>.8) setChip("dec","SCORING","idle"); }},
 {t:"Scores return", d:3.4, x:()=>"This is ordering signal, not recall — the right note is already in the list; the model decides where in the list.",
  a:p=>{ R.cand.forEach((s,i)=>s.show(S.cands[i]+" · "+S.scores[i],C.data,1));
    packet(0,[["d2r",0]],sub(p,0,.5),"res","SCORES");
    R.scores.set(S.scores.join(" · "));
    if(p>.5){ setChip("dec","DONE","done"); setActive("router"); } else setActive("dec"); }},
 {t:"The policy picks the ranking", d:3.8, x:()=>"Auto mode: Mercury's model order wins outright, Jev blends model rank with native rank, any failure falls back to native order. On the published benchmark, stacked ranking put the right note first in 15 of 16 questions.",
  a:p=>{ R.ans.forEach((s,i)=>s.show((i+1)+" · "+S.top[i], i===0?C.data:C.lineHi, sub(p,.1+i*.15,.4+i*.15)));
    R.rst.set("ranking: model order (auto)",C.ink2); setActive("router");
    setChip("answer","RANKED","done");
    if(p>.9) setChip("router","RANKED","done"); }},
 {t:"The answer reaches the agent", d:3.6, x:()=>"The best results return with note paths and snippets, so the agent can open the winner in full. One call, no search loop.",
  a:p=>{ packet(0,[["r2a",0]],sub(p,0,.4),"res","RESULTS");
    if(p<.35) setActive("router"); else setActive("ask");
    if(p>.35){ R.ask.type(S.answer,sub(p,.35,1),"ANSWER",C.data); R.rst.set("results returned",C.ink2); }
    if(p>=1) setChip("router","DONE","done"); }},
 {t:"When the model is down", d:3.6, x:()=>"Mercury's free tier allows twenty requests a minute. A burst or an outage comes back as a 429 — the path where a simpler tool would just fail.",
  a:p=>{ R.ans.forEach(s=>s.show("",C.dim,0));
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.dim,1));
    R.ask.type(S.query,1,"QUERY",C.dim);
    R.rst.set("decision model failed — 429",C.active);
    setChip("answer","EMPTY","idle");
    setChip("router","WAITING","standby");
    setChip("dec","RATE LIMITED","fail"); R.scores.set("no scores",C.active);
    packet(0,[["d2r",0]],sub(p,.15,.85),"fail","429");
    setActive("dec"); }},
 {t:"It retries once", d:3.2, x:()=>"The client waits, then retries once. Transient rate limits clear; a real outage will not.",
  a:p=>{ R.ans.forEach(s=>s.show("",C.dim,0));
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.dim,1));
    R.ask.type(S.query,1,"QUERY",C.dim);
    R.rst.set("retrying once",C.ink2);
    setChip("router","RETRYING","idle");
    setChip("dec","RETRY","idle"); R.scores.set("no scores",C.active);
    packet(0,[["r2d",0]],sub(p,.1,.6),"req","RETRY");
    if(p>.6){ setChip("dec","STILL DOWN","fail"); R.scores.set("still no scores",C.active); }
    if(p<.6) setActive("router"); else setActive("dec"); }},
 {t:"Native order answers instead", d:4.2, x:()=>"If the model stays down, native order answers — same recall, weaker ordering, and the response says fallback: true. The model is never a single point of failure.",
  a:p=>{ R.ask.type(S.query,1,"QUERY",C.dim);
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,1));
    R.ans.forEach((s,i)=>s.show((i+1)+" · "+S.nativeTop[i], i===0?C.data:C.lineHi, sub(p,.2+i*.15,.5+i*.15)));
    R.rst.set("native order · fallback: true",C.ink2);
    R.scores.set("no scores returned");
    setChip("answer","RANKED","done");
    setChip("dec","STANDBY","standby"); setChip("router","FALLBACK","done");
    packet(0,[["r2a",0]],sub(p,.45,.85),"res","RESULTS");
    if(p>.8){ R.ask.type(S.answer,sub(p,.8,1),"ANSWER",C.data); setActive("ask"); }
    else setActive("router"); }},
];
function afterRender(k){ /* derived displays: none */ }
// ===== SCENE END =====
