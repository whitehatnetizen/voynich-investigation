/* Schematic renderer: hatched bar charts, z-bars, log-log & decay sketches, formula + table blocks.
   Graphite on bone, Martian Mono labels, signal orange for the highlighted element. */
(function(){
  const PLATES=window.PLATES;
  const NS="http://www.w3.org/2000/svg";
  const INK="#33342f", DIM="#6a6a62", SIG="#d1571c", CYAN="#1a80b3", OLIVE="#77822f", LINE="#c9c4b4";
  function el(t,a){const e=document.createElementNS(NS,t);for(const k in a)e.setAttribute(k,a[k]);return e;}
  function txt(x,y,s,a){const e=el("text",Object.assign({x,y},a));e.textContent=s;return e;}
  function svg(w,h){const s=el("svg",{viewBox:`0 0 ${w} ${h}`,role:"img"});
    const d=el("defs");
    const p1=el("pattern",{id:"hs",width:7,height:7,patternTransform:"rotate(45)",patternUnits:"userSpaceOnUse"});
    p1.appendChild(el("line",{x1:0,y1:0,x2:0,y2:7,stroke:SIG,"stroke-width":1.5}));
    const p2=el("pattern",{id:"hd",width:7,height:7,patternTransform:"rotate(45)",patternUnits:"userSpaceOnUse"});
    p2.appendChild(el("line",{x1:0,y1:0,x2:0,y2:7,stroke:DIM,"stroke-width":1.3}));
    d.appendChild(p1);d.appendChild(p2);s.appendChild(d);return s;}
  const MONO={"font-family":"'Martian Mono',monospace"};

  // hatched bar chart (horizontal). opts: unit, baseline, band [lo,hi], pct, data [[label,val,hi]]
  function barChart(o){
    const W=560,rowH=34,padL=140,padR=54,top=16,h=top+o.data.length*rowH+30;
    const s=svg(W,h);
    const vals=o.data.map(d=>d[1]);
    let lo=Math.min(0,...vals), hi=Math.max(...vals);
    if(o.band){hi=Math.max(hi,o.band[1]);}
    const span=(hi-lo)||1, x0=padL, x1=W-padR;
    const sx=v=>x0+(v-lo)/span*(x1-x0);
    // band (language reference)
    if(o.band){const bx0=sx(o.band[0]),bx1=sx(o.band[1]);
      s.appendChild(el("rect",{x:bx0,y:top,width:bx1-bx0,height:o.data.length*rowH,fill:OLIVE,opacity:.10}));
      s.appendChild(txt((bx0+bx1)/2,top-4,"LANGUAGE BAND",Object.assign({"text-anchor":"middle","font-size":8,fill:OLIVE},MONO)));}
    // baseline at 0 or given
    const zeroX=sx(o.baseline!=null?o.baseline:lo);
    o.data.forEach((d,i)=>{
      const y=top+i*rowH+6, bh=rowH-14, val=d[1], hlt=d[2];
      const bx=sx(val);
      const x=Math.min(zeroX,bx), w=Math.abs(bx-zeroX);
      s.appendChild(el("rect",{x,y,width:Math.max(w,1),height:bh,fill:hlt?"url(#hs)":"url(#hd)",
        stroke:hlt?SIG:DIM,"stroke-width":1.3}));
      s.appendChild(txt(padL-8,y+bh/2+4,d[0],Object.assign({"text-anchor":"end","font-size":10.5,
        fill:hlt?SIG:INK},MONO)));
      const lab=o.pct?(val*100).toFixed(val<0.1?1:0)+"%":val.toFixed(val%1?2:1);
      // negative bars: value label goes right of the zero axis (that region is empty for the
      // row), so it cannot collide with the row label on the far left
      s.appendChild(txt((bx>=zeroX?bx+5:zeroX+5),y+bh/2+4,lab,Object.assign({"text-anchor":"start",
        "font-size":10,fill:INK},MONO)));
    });
    s.appendChild(el("line",{x1:zeroX,y1:top,x2:zeroX,y2:top+o.data.length*rowH,stroke:INK,"stroke-width":1.5}));
    return wrap(s,o.unit);
  }

  // z-score bars (all positive, single colour ramp, highlight max)
  function zBars(o){
    const W=560,rowH=30,padL=140,padR=44,h=8+o.data.length*rowH+22;
    const s=svg(W,h);const hi=Math.max(...o.data.map(d=>d[1]))||1;
    o.data.forEach((d,i)=>{const y=8+i*rowH,bh=rowH-12;const w=(d[1]/hi)*(W-padL-padR);
      const big=d[1]>=hi*0.66;
      s.appendChild(el("rect",{x:padL,y,width:Math.max(w,1),height:bh,fill:big?"url(#hs)":"url(#hd)",
        stroke:big?SIG:DIM,"stroke-width":1.3}));
      s.appendChild(txt(padL-8,y+bh/2+4,d[0],Object.assign({"text-anchor":"end","font-size":10.5,
        fill:big?SIG:INK},MONO)));
      s.appendChild(txt(padL+w+5,y+bh/2+4,"z="+d[1],Object.assign({"font-size":10,fill:INK},MONO)));});
    s.appendChild(el("line",{x1:padL,y1:4,x2:padL,y2:8+o.data.length*rowH,stroke:INK,"stroke-width":1.5}));
    return wrap(s,o.unit);
  }

  // log-log Zipf sketch: language diagonal, uniform-pool shelf+cliff, stepped shallow monkey
  function zipfSketch(){
    const W=560,H=270,s=svg(W,H),x0=52,x1=W-20,y0=28,y1=H-46;
    s.appendChild(el("line",{x1:x0,y1:y1,x2:x1,y2:y1,stroke:INK,"stroke-width":1.5}));
    s.appendChild(el("line",{x1:x0,y1:y0,x2:x0,y2:y1,stroke:INK,"stroke-width":1.5}));
    s.appendChild(txt(x0-6,y0+4,"freq",Object.assign({"text-anchor":"end","font-size":9,fill:DIM},MONO)));
    s.appendChild(txt(x1,y1+16,"rank →",Object.assign({"text-anchor":"end","font-size":9,fill:DIM},MONO)));
    // language diagonal bundle (Voynich highlighted on top)
    for(let k=0;k<3;k++){const off=k*7;
      s.appendChild(el("line",{x1:x0+off,y1:y0+10+off,x2:x1,y2:y1-14+off*0.4,stroke:DIM,"stroke-width":1.2,opacity:.6}));}
    s.appendChild(el("line",{x1:x0,y1:y0+8,x2:x1,y2:y1-18,stroke:SIG,"stroke-width":2.4}));
    s.appendChild(txt(x1-6,y1-24,"VOYNICH + LANGUAGES (diagonal)",Object.assign({"text-anchor":"end","font-size":9,fill:SIG},MONO)));
    // uniform-pool gibberish: near-horizontal, then cliff at its 1,000-type limit
    const uy=y0+78;
    s.appendChild(el("path",{d:`M ${x0} ${uy} L ${x0+(x1-x0)*0.62} ${uy+8} L ${x0+(x1-x0)*0.66} ${y1-4}`,
      fill:"none",stroke:CYAN,"stroke-width":1.8,"stroke-dasharray":"5 3"}));
    s.appendChild(txt(x0+(x1-x0)*0.05,uy-7,"UNIFORM-POOL GIBBERISH (flat, cliff at rank 1,000: FAILS)",
      Object.assign({"font-size":8.5,fill:CYAN},MONO)));
    // monkey text: stepped head shelf, then a shallower-than-language descent (no cliff)
    const m0=y0+34;
    s.appendChild(el("path",{d:`M ${x0} ${m0} L ${x0+(x1-x0)*0.22} ${m0+4} L ${x0+(x1-x0)*0.26} ${m0+34} `+
      `L ${x0+(x1-x0)*0.46} ${m0+42} L ${x0+(x1-x0)*0.52} ${m0+66} L ${x1} ${y1-38}`,
      fill:"none",stroke:OLIVE,"stroke-width":1.8,"stroke-dasharray":"2 3"}));
    s.appendChild(txt(x1-6,y1-52,"MONKEY TEXT (stepped, shallow: nearly passes)",
      Object.assign({"text-anchor":"end","font-size":8.5,fill:OLIVE},MONO)));
    return wrap(s,"LOG-LOG RANK vs FREQUENCY (SCHEMATIC, SHAPES FROM results DATA)");
  }

  // long-range MI decay: Voynich stays positive, generator + language go to zero/negative
  function decaySketch(){
    const W=560,H=280,s=svg(W,H),x0=48,x1=W-20,y0=24,yz=H-90;
    const sc=v=>yz-v/0.18*(yz-y0);
    s.appendChild(el("line",{x1:x0,y1:yz,x2:x1,y2:yz,stroke:INK,"stroke-width":1.5}));
    s.appendChild(el("line",{x1:x0,y1:y0,x2:x0,y2:H-52,stroke:INK,"stroke-width":1.5}));
    s.appendChild(txt(x0-6,y0+6,"info",Object.assign({"text-anchor":"end","font-size":9,fill:DIM},MONO)));
    s.appendChild(txt(x0-6,yz+4,"0",Object.assign({"text-anchor":"end","font-size":9,fill:DIM},MONO)));
    s.appendChild(txt((x0+x1)/2,H-8,"word distance d →",Object.assign({"text-anchor":"middle","font-size":9,fill:DIM},MONO)));
    // Voynich: high near, decays but stays above zero to far d
    let p="";
    for(let i=0;i<=40;i++){const x=x0+i/40*(x1-x0);const v=0.16*Math.exp(-i/9)+0.02*Math.exp(-i/60);
      p+=(i?" L ":"M ")+x+" "+sc(v);}
    s.appendChild(el("path",{d:p,fill:"none",stroke:SIG,"stroke-width":2.4}));
    s.appendChild(txt(x0+(x1-x0)*0.30,yz-72,"VOYNICH (stays positive to d≈500)",Object.assign({"font-size":9,fill:SIG},MONO)));
    // generator: ~a third, dips negative
    let g="";
    for(let i=0;i<=40;i++){const x=x0+i/40*(x1-x0);const v=0.05*Math.exp(-i/6)-0.02*(1-Math.exp(-i/20));
      g+=(i?" L ":"M ")+x+" "+sc(v);}
    s.appendChild(el("path",{d:g,fill:"none",stroke:DIM,"stroke-width":1.6,"stroke-dasharray":"5 3"}));
    // language: negative
    s.appendChild(el("path",{d:`M ${x0} ${yz-6} Q ${(x0+x1)/2} ${yz+18} ${x1} ${yz+14}`,fill:"none",
      stroke:CYAN,"stroke-width":1.4,"stroke-dasharray":"2 3"}));
    // legend row along the bottom, clear of all three curves and the axis label
    s.appendChild(txt(x0,yz+42,"GENERATOR (~a third, then negative)",Object.assign({"font-size":9,fill:DIM},MONO)));
    s.appendChild(txt(x1,yz+42,"SINGLE REAL WORK (≈0 / negative)",Object.assign({"text-anchor":"end","font-size":9,fill:CYAN},MONO)));
    return wrap(s,"CROSS-WORD MUTUAL INFORMATION vs DISTANCE (SCHEMATIC)");
  }

  function wrap(s,cap){const f=document.createElement("figure");f.appendChild(s);
    if(cap){const c=document.createElement("figcaption");c.textContent="FIG · "+cap;f.appendChild(c);}return f;}

  function formulaBlock(lines){const wrapEl=document.createElement("div");
    lines.forEach(([f,n])=>{const d=document.createElement("div");d.className="formula";
      d.innerHTML=esc(f)+'  <span class="n">// '+esc(n)+'</span>';wrapEl.appendChild(d);});return wrapEl;}

  function correctionsTable(rows){const t=document.createElement("div");t.className="readings";
    t.innerHTML='<div class="h">Numbers corrected in the re-audit</div>';
    rows.forEach(([what,was,now])=>{const r=document.createElement("div");r.className="r";
      r.style.gridTemplateColumns="1fr 90px 110px";
      r.innerHTML=`<div>${esc(what)}</div><div class="mono" style="color:var(--dim)">${esc(was)}</div>`+
        `<div class="mono" style="color:var(--sig);font-weight:700">${esc(now)}</div>`;t.appendChild(r);});
    return t;}

  // generic titled table: {title, cols:"1fr 90px ...", rows:[[cell,...]]}; last cell rendered bold+signal
  function rulesTable(o){const t=document.createElement("div");t.className="readings";
    t.innerHTML='<div class="h">'+esc(o.title)+'</div>';
    o.rows.forEach(cells=>{const r=document.createElement("div");r.className="r";
      r.style.gridTemplateColumns=o.cols;
      r.innerHTML=cells.map((c,i)=>i===cells.length-1
        ?`<div class="mono" style="color:var(--sig);font-weight:700">${esc(c)}</div>`
        :(i===0?`<div class="mono" style="font-weight:700">${esc(c)}</div>`:`<div>${esc(c)}</div>`)).join("");
      t.appendChild(r);});
    return t;}

  function esc(s){return String(s).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}

  /* Wikipedia links for technical terms. Terms are matched against the ESCAPED text
     (hence "&amp;"), first occurrence per plate, deduped by target URL. */
  const WIKI=[
    ["second-order character entropy","Conditional_entropy"],
    ["conditional entropy","Conditional_entropy"],
    ["Damerau-Levenshtein","Damerau%E2%80%93Levenshtein_distance"],
    ["Timm &amp; Schinner","https://doi.org/10.1080/01611194.2019.1596999"],
    ["substitution cipher","Substitution_cipher"],
    ["constructed language","Constructed_language"],
    ["Linnaean binomials","Binomial_nomenclature"],
    ["mutual information","Mutual_information"],
    ["null distributions","Null_distribution"],
    ["null distribution","Null_distribution"],
    ["standard deviation","Standard_deviation"],
    ["shuffle control","Permutation_test"],
    ["scribal hands","Scribe"],
    ["edit distance","Edit_distance"],
    ["tokenisation","Text_segmentation"],
    ["Zipf's law","Zipf%27s_law"],
    ["morphology","Morphology_(linguistics)"],
    ["collocation","Collocation"],
    ["Esperanto","Esperanto"],
    ["bootstrap","Bootstrapping_(statistics)"],
    ["register","Register_(sociolinguistics)"],
    ["Beinecke","Beinecke_Rare_Book_%26_Manuscript_Library"],
    ["log-log","Log%E2%80%93log_plot"],
    ["entropy","Entropy_(information_theory)"],
    ["shuffle","Permutation_test"],
    ["Markov","Markov_chain"],
    ["cipher","Cipher"],
    ["herbal","Herbal"],
    ["zodiac","Zodiac"],
    ["folios","Folio"],
    ["folio","Folio"],
    ["syntax","Syntax"],
    ["glyph","Glyph"],
    ["abjad","Abjad"],
    ["Heaps","Heaps%27_law"],
    ["Zipf","Zipf%27s_law"],
    ["h2","Conditional_entropy"]
  ];
  const WMAP={}; WIKI.forEach(([t,u])=>{WMAP[t.toLowerCase()]=u;});
  const WRX=new RegExp("\\b(?:"+WIKI.map(([t])=>t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")).join("|")+")\\b","gi");
  function linkify(escaped, used){
    return escaped.replace(WRX,m=>{
      const u=WMAP[m.toLowerCase()];
      if(!u||used.has(u))return m;
      used.add(u);
      const href=u.startsWith("http")?u:"https://en.wikipedia.org/wiki/"+u;
      return '<a class="wk" href="'+href+'" target="_blank" rel="noopener">'+m+'</a>';
    });
  }

  function figure(fig){
    if(!fig)return null;
    if(fig.type==="bars")return barChart(fig);
    if(fig.type==="zbars")return zBars(fig);
    if(fig.type==="zipf")return zipfSketch();
    if(fig.type==="decay")return decaySketch();
    if(fig.type==="formula")return formulaBlock(fig.lines);
    if(fig.type==="corrections")return correctionsTable(fig.data);
    if(fig.type==="rules")return rulesTable(fig);
    return null;
  }

  function readingsBlock(){
    const t=document.createElement("div");t.className="readings";
    t.innerHTML='<div class="h">Two readings survive, differing almost only in the labels</div>'+
      '<div class="r"><div class="num">1</div><div><strong>Meaningless auto-generation.</strong> A scribe following a practiced word-building habit, vocabulary drifting slowly as the pictures change. The leading account.</div></div>'+
      '<div class="r"><div class="num">2</div><div><strong>A formulaic catalogue.</strong> Real content, but so templated that its statistics mimic generation.</div></div>';
    return t;
  }

  function plate(p,i){
    const el2=(t,c,h)=>{const e=document.createElement(t);if(c)e.className=c;if(h!=null)e.innerHTML=h;return e;};
    const used=new Set();
    const lk=s=>linkify(esc(s),used);
    const sec=el2("section","plate");sec.id="s"+(i+1);
    const dwg=el2("div","dwg");
    dwg.appendChild(el2("span","lbl caps",esc(p.dwg)));
    dwg.appendChild(el2("span","sheet",((i+1)<10?"0":"")+(i+1)+" / "+PLATES.length));
    sec.appendChild(dwg);
    if(p.kind==="conclusion"){
      const row=el2("div","row conc");
      const left=el2("div","block",'<span class="tag">Established</span><ol>'+
        p.established.map(s=>'<li>'+lk(s)+'</li>').join("")+'</ol>');
      const right=el2("div","block res",'<span class="tag">Still open</span><ul>'+
        p.open.map(s=>'<li>'+lk(s)+'</li>').join("")+'</ul>');
      row.appendChild(left);row.appendChild(right);
      sec.appendChild(row);
      sec.appendChild(el2("div","next",'<span class="tag">Conclusion</span>'+
        p.next.split("\n\n").map(x=>'<p>'+lk(x)+'</p>').join("")));
      return sec;
    }
    const hyp=el2("div","hyp",'<span class="tag">Hypothesis</span><p>'+lk(p.hyp)+'</p>');
    sec.appendChild(hyp);
    const row=el2("div","row");
    const left=el2("div","block",'<span class="tag">How we tested it</span><p>'+lk(p.test)+'</p>');
    const fig=figure(p.fig); if(fig)left.appendChild(fig);
    const fig2=figure(p.fig2); if(fig2)left.appendChild(fig2);
    const right=el2("div","block res",'<span class="tag">Result</span>'+
      '<span class="verdict '+p.verdict+'">'+esc(p.verdictText)+'</span><p>'+lk(p.res)+'</p>');
    if(i===9)right.appendChild(readingsBlock());
    row.appendChild(left);row.appendChild(right);
    sec.appendChild(row);
    if(p.plain)p.plain.forEach(a=>{
      const d=document.createElement("details");d.className="algo plain";
      const su=document.createElement("summary");su.textContent="IN PLAIN TERMS · "+a.t;d.appendChild(su);
      const body=document.createElement("div");body.className="plainbody";body.innerHTML=a.h;d.appendChild(body);
      sec.appendChild(d);
    });
    if(p.algo)p.algo.forEach(a=>{
      const d=document.createElement("details");d.className="algo";
      const su=document.createElement("summary");su.textContent="ALGORITHM · "+a.t;d.appendChild(su);
      const pre=document.createElement("pre");pre.textContent=a.c;d.appendChild(pre);
      sec.appendChild(d);
    });
    sec.appendChild(el2("div","next",'<span class="tag">Next question</span> '+lk(p.next)));
    return sec;
  }

  const main=document.getElementById("main");
  const toc=document.getElementById("toc");
  PLATES.forEach((p,i)=>{
    main.appendChild(plate(p,i));
    const a=document.createElement("a");a.href="#s"+(i+1);
    a.textContent=(i+1<10?"0":"")+(i+1)+" "+p.dwg.split("· ")[1].split(" ").slice(0,2).join(" ");
    toc.appendChild(a);
  });
  const ra=document.createElement("a");ra.href="#refs";ra.textContent="REFERENCES";
  toc.appendChild(ra);
})();
