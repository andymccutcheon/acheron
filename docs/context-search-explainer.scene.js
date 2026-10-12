// ===== SCENE START =====
const THEME = "pattern";
const SCENE={
  title:"How a question becomes a ranked answer",
  code:"EXPLAINER 03", kicker:"CONTEXT // SEARCH PATH",
  note:"Only Mercury rank 1 is shown. Benchmark ranks and top-1 counts come from the recorded 16-question, 23-note demo corpus.",
  crosshairs:[],
  legend:[["REQUEST",C.request],["RESULT / DATA",C.data],["ACTIVE",C.active],["FAILED",C.fail]],
  introTitle:"One query through the context layer",
  introText:"Eleven steps from a Tidepool benchmark question to a ranked answer, including model failure. Step with the arrow keys or add ?autoplay to the URL.",
};
const FOLDERS=["concepts · 5","decisions · 6","guides · 3","incidents · 3","meetings · 3","people · 3"];
const SCENARIOS=[
  {label:"Mobile sunset question",
   query:["Why did Tidepool drop","its mobile app?"],
   cands:["2025-08-04 Weekly","Maya Chen","Priya Nair","Decision - Local-first, no cloud sync"],
   scores:["high","review","review","high"],
   winner:"Decision - Drop the native mobile app",
   nativeTop:["2025-08-04 Weekly","Maya Chen","Priya Nair","Decision - Local-first, no cloud sync"],
   answer:["Mobile sync took about half","of each release cycle; the relay","added an unwanted server dependency."]},
];
const R={};
function buildScene(){
  panel("agent",{x:40,y:110,w:230,h:170,code:"P-01",title:"AGENT",chip:"IDLE"});
  icon("agent","person",78,192,0.9);
  text("agent",112,158,"OpenCode","body2",{maxW:146});
  text("agent",112,180,"Claude Code","body2",{maxW:146});
  text("agent",112,202,"one MCP server","body2",{maxW:146});
  panel("ask",{x:40,y:300,w:360,h:120,title:null});
  R.ask=bubble("ask");
  panel("answer",{x:40,y:430,w:360,h:160,code:"R-01",title:"ANSWER",chip:"EMPTY"});
  R.ans=[0,1,2,3].map(i=>slot("answer",56,474+i*28,328,24));

  panel("router",{x:480,y:96,w:330,h:200,code:"M-01",title:"ACHERON",chip:"STANDBY"});
  R.rst=dynText("router",496,160,"body2",{maxW:298});
  R.cand=[0,1,2,3].map(i=>slot("router",496,176+i*28,298,24));

  panel("bm",{x:900,y:96,w:300,h:150,code:"S-01",title:"BASIC MEMORY",chip:"WATCHING"});
  icon("bm","db",1168,196,0.8);
  text("bm",916,150,"HTTP MCP · hybrid search","body2",{maxW:230});
  text("bm",916,172,"SQLite index · file watcher","body2",{maxW:230});
  text("bm",916,194,"findable in under a minute","body2",{maxW:230});
  panel("dec",{x:900,y:290,w:300,h:150,code:"S-02",title:"DECISION MODEL",chip:"STANDBY"});
  text("dec",916,344,"OpenRouter · Mercury Decide","body2",{maxW:268});
  text("dec",916,366,"scores candidates 0–3","body2",{maxW:268});
  R.scores=dynText("dec",916,392,"out",{maxW:268});

  panel("lib",{x:480,y:470,w:720,h:120,code:"L-01",title:"TIDEPOOL DEMO LIBRARY",chip:"23 NOTES"});
  text("lib",496,508,"eval/demo/notes · synthetic corpus","body2",{maxW:400});
  R.lib=FOLDERS.map((t,i)=>slot("lib",500+(i%3)*230,524+Math.floor(i/3)*28,210,26));

  wire("a2r","M400,340 C440,340 440,150 480,150");
  wire("r2a","M480,210 C440,210 440,380 400,380");
  wire("r2b","M810,150 L900,150");
  wire("b2r","M900,200 L810,200");
  wire("r2d","M810,240 C860,240 860,340 900,340");
  wire("d2r","M900,390 C860,390 860,270 810,270");
  wire("bl","M700,470 C855,470 855,220 900,220",{both:true});
}
const STEPS=[
 {t:"The demo corpus, indexed", d:3.6, x:()=>"Twenty-three markdown notes for a fictional photo-sync project, grouped by folder. Basic Memory keeps a local hybrid index over them and refreshes when files change.",
  a:p=>{ setActive("lib");
    R.lib.forEach((s,i)=>s.show(FOLDERS[i],C.lineHi,sub(p,.08+i*.12,.35+i*.12)));
    setChip("bm","WATCHING","idle"); setChip("dec","STANDBY","standby"); setChip("router","STANDBY","standby");
    setChip("agent","IDLE","idle"); setChip("answer","EMPTY","idle"); }},
 {t:"A question arrives", d:3.4, x:()=>"Any agent calls the one first-party tool, context_search. Every other storage tool stays proxied under its engine name.",
  a:p=>{ R.ask.type(S.query,sub(p,0,.55),"QUERY",C.request);
    packet(0,[["a2r",0]],sub(p,.5,1),"req","context_search");
    if(p<.55) setActive("ask"); else setActive("router"); }},
 {t:"Hybrid search on the engine", d:3.4, x:()=>"Acheron forwards search_notes to the long-running Basic Memory service. Candidates come from the engine's native hybrid search, not from the decision model.",
  a:p=>{ R.rst.set("search_notes · tidepool · top 10",C.ink2);
    packet(0,[["r2b",0]],sub(p,.15,.85),"req");
    setActive("router"); if(p>.7) setChip("bm","SEARCHING","idle"); }},
 {t:"Ten candidates return", d:3.6, x:()=>"Up to ten notes return with paths and snippets. The right answer is usually already in the list; reranking only reorders.",
  a:p=>{ packet(0,[["b2r",0]],sub(p,0,.45),"res","10 NOTES");
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,sub(p,.35+i*.12,.6+i*.12)));
    if(p>.6){ setChip("bm","10 FOUND","done"); R.rst.set("10 candidates · answer native rank 7",C.ink2); setActive("router"); }
    else setActive("bm"); }},
 {t:"The model scores each note", d:3.6, x:()=>"When an OpenRouter key is set, Mercury Decide scores each candidate on usefulness. Note text is untrusted evidence, not instructions.",
  a:p=>{ R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,1));
    packet(0,[["r2d",0]],sub(p,.1,.75),"req","SCORE");
    setActive("dec"); R.scores.set("scoring 10 candidates");
    if(p>.8) setChip("dec","SCORING","idle"); }},
 {t:"Scores return", d:3.4, x:()=>"Scores are ordering signal. They do not change which notes were retrieved; the score labels shown here are illustrative.",
  a:p=>{ R.cand.forEach((s,i)=>s.show(S.cands[i]+" · "+S.scores[i],C.data,1));
    packet(0,[["d2r",0]],sub(p,0,.5),"res","SCORES");
    R.scores.set(S.scores.join(" · "));
    if(p>.5){ setChip("dec","DONE","done"); setActive("router"); } else setActive("dec"); }},
 {t:"Model order wins", d:3.8, x:()=>"In auto mode with Mercury, model order wins. On the unstacked benchmark (16 questions, hand labels), Mercury put the labeled note first in 14 of 16; native hybrid alone reached 7 of 16.",
  a:p=>{ R.ans[0].show("1 · "+S.winner,C.data,sub(p,.1,.4));
    R.ans[1].show("9 other candidates reordered",C.lineHi,sub(p,.25,.55));
    R.ans[2].show("Only the winner's rank is evidenced",C.lineHi,sub(p,.4,.7));
    R.ans[3].show("",C.dim,0);
    R.rst.set("ranking: model · fallback false",C.ink2); setActive("router");
    setChip("answer","RANKED","done");
    if(p>.9) setChip("router","RANKED","done"); }},
 {t:"Results reach the agent", d:3.6, x:()=>"The response lists ranked notes with paths and snippets so the agent can open the winner. One call, no search loop.",
  a:p=>{ packet(0,[["r2a",0]],sub(p,0,.4),"res","RESULTS");
    if(p<.35) setActive("router"); else setActive("ask");
    if(p>.35){ R.ask.type(S.answer,sub(p,.35,1),"ANSWER",C.data); R.rst.set("Decision - Drop the native mobile app",C.ink2); }
    if(p>=1) setChip("router","DONE","done"); }},
 {t:"When the model rate-limits", d:3.6, x:()=>"A 429 from the Decisions API is a reranker failure, not a storage outage. Acheron does not pretend the engine survived an outage.",
  a:p=>{ R.ans.forEach(s=>s.show("",C.dim,0));
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.dim,1));
    R.ask.type(S.query,1,"QUERY",C.dim);
    R.rst.set("decision model · 429",C.fail);
    setChip("answer","EMPTY","idle");
    setChip("router","WAITING","standby");
    setChip("dec","RATE LIMITED","fail"); R.scores.set("no scores",C.fail);
    packet(0,[["d2r",0]],sub(p,.15,.85),"fail","429");
    setActive("dec"); }},
 {t:"One retry", d:3.2, x:()=>"The client waits, then retries once on 429 or 5xx. A persistent outage still fails open after that.",
  a:p=>{ R.ans.forEach(s=>s.show("",C.dim,0));
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.dim,1));
    R.ask.type(S.query,1,"QUERY",C.dim);
    R.rst.set("retrying once",C.ink2);
    setChip("router","RETRYING","idle");
    setChip("dec","RETRY","idle"); R.scores.set("awaiting scores",C.ink2);
    packet(0,[["r2d",0]],sub(p,.1,.6),"req","RETRY");
    if(p>.6){ setChip("dec","STILL DOWN","fail"); R.scores.set("still no scores",C.fail); }
    if(p<.6) setActive("router"); else setActive("dec"); }},
 {t:"Native order, fallback true", d:4.2, x:()=>"If the model stays down, results keep native hybrid order. The response sets fallback: true and ranking: native. Recall stays; ordering weakens.",
  a:p=>{ R.ask.type(S.query,1,"QUERY",C.dim);
    R.cand.forEach((s,i)=>s.show(S.cands[i],C.data,1));
    R.ans.forEach((s,i)=>s.show((i+1)+" · "+S.nativeTop[i], i===0?C.data:C.lineHi, sub(p,.2+i*.15,.5+i*.15)));
    R.rst.set("native order · fallback: true",C.ink2);
    R.scores.set("no scores returned",C.ink2);
    setChip("answer","RANKED","done");
    setChip("dec","STANDBY","standby"); setChip("router","FALLBACK","done");
    packet(0,[["r2a",0]],sub(p,.45,.85),"res","RESULTS");
    if(p>.8){ R.ask.type(S.answer,sub(p,.8,1),"ANSWER",C.data); setActive("ask"); }
    else setActive("router"); }},
];
function afterRender(k){ /* derived displays: none */ }
// ===== SCENE END =====
