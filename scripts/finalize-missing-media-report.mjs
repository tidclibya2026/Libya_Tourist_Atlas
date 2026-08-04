import fs from 'node:fs';
const parse=line=>{const out=[];let cur='',quoted=false;for(let i=0;i<line.length;i++){const c=line[i];if(c==='"'){if(quoted&&line[i+1]==='"'){cur+='"';i++}else quoted=!quoted}else if(c===','&&!quoted){out.push(cur);cur=''}else cur+=c}out.push(cur);return out};
const q=v=>'"'+String(v??'').replace(/"/g,'""')+'"';
const zLines=fs.readFileSync('docs/zumit-media-audit.csv','utf8').trim().split(/\r?\n/),headers=parse(zLines[0]),zRows=zLines.slice(1).map(line=>Object.fromEntries(headers.map((h,i)=>[h,parse(line)[i]||'']))).map(row=>({...row,result:'decode_failed_browser'}));
fs.writeFileSync('docs/zumit-media-audit.csv',[headers.map(q).join(','),...zRows.map(r=>headers.map(h=>q(r[h])).join(','))].join('\n')+'\n');
const http=fs.readFileSync('docs/popup-media-http-test.csv','utf8').trim().split(/\r?\n/),failed=http.filter((line,i)=>i===0||!/,"ok"$/.test(line));
const missingHeader='"layer","placemark","raw_path","actual_filesystem_path","resolved_url","http_status","result"';
fs.writeFileSync('docs/missing-popup-media.csv',[missingHeader,...zRows.map(r=>headers.map(h=>q(r[h])).join(',')),...failed.slice(1).map(line=>{const p=parse(line);return [p[0],p[1],p[2],'',p[3],p[4],p[5]].map(q).join(',')})].join('\n')+'\n');
console.log(`Missing media report: ${zRows.length} Zumit decode failures + ${failed.length-1} sampled HTTP failures.`);
