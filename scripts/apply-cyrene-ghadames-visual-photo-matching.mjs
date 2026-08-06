import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const root = process.cwd();
const geoPath = path.join(root, 'data/layers/world-heritage.geojson');
const geo = JSON.parse(fs.readFileSync(geoPath, 'utf8'));
const byId = new Map(geo.features.map(feature => [feature.properties?.id, feature]));

const confirmed = [
  {
    site: 'cyrene', id: 'WH-LY-003-C0023', subject: 'البازيليكا البيزنطية', confidence: 'high',
    files: ['450A2244.JPG', '450A2245.JPG', '450A2246.JPG', '450A2250.JPG', '450A2251.JPG'],
    reason: 'تتابع تصويري واحد يُظهر صحن البازيليكا وصفوف الأعمدة ونهاية المبنى نصف الدائرية.'
  },
  {
    site: 'cyrene', id: 'WH-LY-003-C0001', subject: 'مسرح شحات الأثري', confidence: 'high',
    files: ['450A2252.JPG', 'شحات 4.jpg'],
    reason: 'المدرج نصف الدائري الحجري ظاهر بوضوح في الصورتين.'
  },
  {
    site: 'cyrene', id: 'WH-LY-003-C0016', subject: 'نبع أبولو', confidence: 'high',
    files: ['اااااا.jpg'],
    reason: 'الصورة تحمل تعريف Fountain of Apollo وتُظهر واجهة النبع الصخرية.'
  },
  {
    site: 'cyrene', id: 'WH-LY-003-C0022', subject: 'السوق اليوناني القديم (الأغورا)', confidence: 'high',
    files: ['450A2269.JPG', '450A2270.JPG', '450A2277.JPG', '450A2281.JPG', '450A2282.JPG'],
    reason: 'سلسلة متصلة داخل الأغورا، وإحدى الصور توثق لوحة الموقع المكتوب عليها Greek Agora.'
  }
];

const slugById = {
  'WH-LY-003-C0023': 'byzantine-basilica',
  'WH-LY-003-C0001': 'archaeological-theatre',
  'WH-LY-003-C0016': 'fountain-of-apollo',
  'WH-LY-003-C0022': 'greek-agora'
};

const sourceFolder = { cyrene: 'شحات', ghadames: 'غدامس' };
const publishedRoot = site => path.join(root, 'assets/media/LIBYA/heritage', site, 'published/features');
const rel = absolute => path.relative(root, absolute).replaceAll('\\', '/');

for (const match of confirmed) {
  const feature = byId.get(match.id);
  if (!feature) throw new Error(`Missing feature ${match.id}`);
  const targetDir = path.join(publishedRoot(match.site), slugById[match.id]);
  fs.mkdirSync(targetDir, { recursive: true });
  const images = match.files.map((filename, index) => {
    const source = path.join(root, sourceFolder[match.site], filename);
    if (!fs.existsSync(source)) throw new Error(`Missing source image ${source}`);
    const extension = path.extname(filename).toLowerCase();
    const target = path.join(targetDir, `${slugById[match.id]}-${String(index + 1).padStart(3, '0')}${extension}`);
    fs.copyFileSync(source, target);
    return rel(target);
  });
  Object.assign(feature.properties, {
    local_images: images,
    image_count: images.length,
    image_match_type: 'exact_feature',
    image_match_confidence: match.confidence,
    image_source: 'official_center_media_visual_review',
    image_owner_ar: 'مركز المعلومات والتوثيق السياحي',
    image_rights_status: 'institutional_ownership',
    image_review_status: 'confirmed_visual_match'
  });
}

fs.writeFileSync(geoPath, JSON.stringify(geo, null, 2) + '\n');

const subjects = {
  cyrene: {
    '450A2244.JPG': 'صف أعمدة داخل مبنى بازيليكي', '450A2245.JPG': 'صحن بازيليكا وأعمدة',
    '450A2246.JPG': 'نهاية نصف دائرية وصف أعمدة بازيليكا', '450A2250.JPG': 'رواق بازيليكا',
    '450A2251.JPG': 'رواق بازيليكا', '450A2252.JPG': 'مدرج مسرح حجري نصف دائري',
    '450A2254.JPG': 'بوابة أثرية ذات أعمدة', '450A2255.JPG': 'بوابة أثرية ذات أعمدة',
    '450A2259.JPG': 'أرضية فسيفساء', '450A2265.JPG': 'نحت معماري على عارضة حجرية',
    '450A2266.JPG': 'تماثيل هيرمية فوق جدار', '450A2267.JPG': 'تماثيل هيرمية فوق جدار',
    '450A2268.JPG': 'مشهد طبيعي كثيف الأشجار', '450A2269.JPG': 'أعمدة ومنشآت الأغورا',
    '450A2270.JPG': 'لوحة تعريف Greek Agora', '450A2277.JPG': 'صف أعمدة الأغورا',
    '450A2281.JPG': 'منشآت وأعمدة الأغورا', '450A2282.JPG': 'منشآت وأعمدة الأغورا',
    '450A2284.JPG': 'تفصيل عمود أثري', '450A2285.JPG': 'عارضة حجرية أثرية',
    '450A2286.JPG': 'بوابة معمدة', '450A2310.JPG': 'منطقة أثرية مطلة على السهل',
    '450A2321.JPG': 'أعمدة في المصطبة السفلية', '450A2323.JPG': 'أعمدة في المصطبة السفلية',
    '450A2324.JPG': 'مبنى معمد في المصطبة السفلية', '450A2325.JPG': 'مبنى معمد بين الأشجار',
    '450A2326.JPG': 'مبنى أثري صغير ذو مدخل', 'DJI_0722.JPG': 'منظر جوي للطريق ومحيط الموقع',
    'DJI_0724.JPG': 'منظر جوي للطريق ومحيط الموقع', 'FB_IMG_1648770111714.jpg': 'منظر جوي لمعبد كبير',
    'images-11-1.jpg': 'منظر عام لأعمدة وآثار قورينا', 'images-5.jpg': 'نقوش وتماثيل حجرية',
    'اااااا.jpg': 'نبع أبولو مع تسمية ظاهرة', 'شحات 4.jpg': 'مدرج مسرح حجري',
    'معبد زيوس.jpeg': 'معبد زيوس',
  },
  ghadames: {
    '1300130.jpg': 'ممر مسقوف داخل المدينة القديمة', '1459892.jpg': 'غرفة غدامسية مزخرفة',
    '21311866.jpg': 'أقواس وممر في المدينة القديمة', '21311876.jpg': 'ممر مسقوف في المدينة القديمة',
    '21311890.jpg': 'باب غدامسي مزخرف', '21311896.jpg': 'باب غدامسي مزخرف',
    '274492.jpg': 'ممر مسقوف في المدينة القديمة', '274526.jpg': 'غرفة غدامسية مزخرفة',
    '274527.jpg': 'باب غدامسي مزخرف', '27860001.jpg': 'ممر مسقوف في المدينة القديمة',
    '311970_425424474161106_853650539_n.jpg': 'غرفة غدامسية مزخرفة',
    '311970_425424474161106_853650539_n (2).jpg': 'نسخة مطابقة لغرفة غدامسية مزخرفة',
    '450A4725.JPG': 'قوس وممر في المدينة القديمة', '450A4729.JPG': 'مئذنة وممر خارجي',
    '450A4841.JPG': 'واجهة مبنى ديني أبيض غير محدد', '450A4869.JPG': 'سطوح وواحة غدامس',
    '450A4915.JPG': 'قاعة صلاة غير محددة', '450A4922.JPG': 'محراب مسجد غير محدد',
    '450A4964.JPG': 'ممر مسقوف في المدينة القديمة', '450A5010.JPG': 'باب داخلي مزخرف',
    '450A5043.JPG': 'درج ومدخل بيت طيني', '450A5140.JPG': 'ممر مسقوف في المدينة القديمة',
    '450A5140 (2).JPG': 'نسخة مطابقة لممر مسقوف', '450A5211.JPG': 'زي تراثي غدامسي',
    '46137521.jpg': 'نافذة مزخرفة داخل ممر', '61.jpg': 'واجهة مبنى ديني أبيض غير محدد',
    '62.jpg': 'مئذنة وممر خارجي', '63.JPG': 'واجهة مبنى ديني أبيض غير محدد',
    '65.JPG': 'ساحة ومبنى طيني', '7206439.jpg': 'درج ومدخل في المدينة القديمة',
    '84220331.jpg': 'مدخل مزخرف', 'Ali (287).jpg': 'واجهة مبنى ديني أبيض غير محدد',
    'hosting-ee87349515.jpg': 'غرفة غدامسية مزخرفة', 'عين الفرس.jpg': 'عين الفرس',
    'غدامس  1.jpg': 'واجهة مبنى ديني أبيض غير محدد', 'غدامس  3.jpg': 'ممر خارجي في المدينة القديمة',
    'غدامس  4.jpg': 'مئذنة وممر خارجي', 'غدامس  5.jpg': 'ممر مسقوف في المدينة القديمة'
  }
};

const csvEscape = value => `"${String(value ?? '').replaceAll('"', '""')}"`;
for (const site of ['cyrene', 'ghadames']) {
  const rows = [['source_filename','sha256','visual_subject','matched_feature_id','matched_feature_name_ar','match_type','confidence','review_status','notes']];
  const folder = path.join(root, sourceFolder[site]);
  for (const filename of fs.readdirSync(folder).filter(name => /\.(jpe?g|png)$/i.test(name)).sort((a,b) => a.localeCompare(b,'ar'))) {
    const bytes = fs.readFileSync(path.join(folder, filename));
    const match = confirmed.find(item => item.site === site && item.files.includes(filename));
    const existingExact = (site === 'cyrene' && filename === 'معبد زيوس.jpeg')
      ? { id: 'WH-LY-003-C0021', subject: 'معبد زيوس', confidence: 'high', reason: 'اسم الملف والمحتوى البصري يطابقان المعبد.' }
      : (site === 'ghadames' && filename === 'عين الفرس.jpg')
        ? { id: 'WH-LY-005-C0004', subject: 'عين الفرس', confidence: 'high', reason: 'اسم الملف والحوض المائي الظاهر يطابقان عين الفرس.' }
        : null;
    const selected = match || existingExact;
    const feature = selected ? byId.get(selected.id) : null;
    rows.push([
      filename, crypto.createHash('sha256').update(bytes).digest('hex'), subjects[site][filename] || 'مشهد عام من الموقع دون علامة مميزة',
      selected?.id || '', feature?.properties?.name_ar || '', selected ? 'exact_feature' : 'unmatched',
      selected?.confidence || 'none', selected ? 'confirmed' : 'reviewed_unmatched',
      selected?.reason || 'تمت المراجعة بصريًا؛ لا توجد علامة كافية لربط الصورة بنقطة متخصصة دون تخمين.'
    ]);
  }
  const output = path.join(root, `docs/media-linkage/${site}-visual-image-classification.csv`);
  fs.writeFileSync(output, rows.map(row => row.map(csvEscape).join(',')).join('\n') + '\n');
}

const report = `# مراجعة المطابقة البصرية لصور شحات وغدامس\n\n` +
`## النتيجة\n\nتمت مراجعة كل صور مجلدي شحات وغدامس بصريًا. نُشرت المطابقات التي تحتوي على دليل بصري مباشر فقط، وبقيت الصور العامة أو الملتبسة غير مرتبطة بالنقاط المتخصصة.\n\n` +
`## المطابقات الجديدة المؤكدة في شحات\n\n` + confirmed.map(item => `- ${item.id} — ${item.subject}: ${item.files.length} صورة. ${item.reason}`).join('\n') +
`\n\n## غدامس\n\n- بقيت صورة عين الفرس مطابقة دقيقة للنقطة WH-LY-005-C0004.\n- لم تُنشر مطابقة جديدة: صور المسجد الأبيض/المدرسة والممرات والبيوت لا تحمل علامات كافية لتحديد النقطة المقصودة دون تخمين.\n- بقيت الصور العامة محصورة في الموقع الرئيسي، وبقية النقاط على placeholder.\n`;
fs.writeFileSync(path.join(root, 'docs/cyrene-ghadames-visual-photo-matching-report.md'), report);

console.log(`CONFIRMED_NEW_FEATURES=${confirmed.length}`);
console.log(`CONFIRMED_NEW_IMAGES=${confirmed.reduce((sum, item) => sum + item.files.length, 0)}`);
