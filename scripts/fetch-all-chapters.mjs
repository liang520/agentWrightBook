import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';
import { join } from 'path';

const FONT_MAP = {58670:'0',58413:'1',58678:'2',58371:'3',58353:'4',58480:'5',58359:'6',58449:'7',58540:'8',58692:'9',58611:'的',58590:'一',58398:'是',58422:'了',58657:'我',58666:'不',58562:'人',58345:'在',58510:'他',58496:'有',58654:'这',58441:'个',58493:'上',58714:'们',58618:'来',58528:'到',58620:'时',58403:'大',58461:'地',58481:'为',58700:'子',58708:'中',58503:'你',58442:'说',58639:'生',58506:'国',58663:'年',58436:'着',58563:'就',58391:'那',58357:'和',58354:'要',58695:'她',58372:'出',58696:'也',58551:'得',58445:'里',58408:'后',58599:'自',58424:'以',58394:'会',58348:'家',58426:'可',58673:'下',58417:'而',58556:'过',58603:'天',58565:'去',58604:'能',58522:'对',58632:'小',58622:'多',58350:'然',58605:'于',58617:'心',58401:'学',58637:'么',58684:'之',58382:'都',58464:'好',58487:'看',58693:'起',58608:'发',58392:'当',58474:'没',58601:'成',58355:'只',58573:'如',58499:'事',58469:'把',58361:'还',58698:'用',58489:'第',58711:'样',58457:'道',58635:'想',58492:'作',58647:'种',58623:'开',58521:'美',58609:'总',58530:'从',58665:'无',58652:'情',58676:'己',58456:'面',58581:'最',58509:'女',58488:'但',58363:'现',58685:'前',58396:'些',58523:'所',58471:'同',58485:'日',58613:'手',58533:'又',58589:'行',58527:'意',58593:'动',58699:'方',58707:'期',58414:'它',58596:'头',58570:'经',58660:'长',58364:'儿',58526:'回',58501:'位',58638:'分',58404:'爱',58677:'老',58535:'因',58629:'很',58577:'给',58606:'名',58497:'法',58662:'间',58479:'斯',58532:'知',58380:'世',58385:'什',58405:'两',58644:'次',58578:'使',58505:'身',58564:'者',58412:'被',58686:'高',58624:'已',58667:'亲',58607:'其',58616:'进',58368:'此',58427:'话',58423:'常',58633:'与',58525:'活',58543:'正',58418:'感',58597:'见',58683:'明',58507:'问',58621:'力',58703:'理',58438:'尔',58536:'点',58384:'文',58484:'几',58539:'定',58554:'本',58421:'公',58347:'特',58569:'做',58710:'外',58574:'孩',58375:'相',58645:'西',58592:'果',58572:'走',58388:'将',58370:'月',58399:'十',58651:'实',58546:'向',58504:'声',58419:'车',58407:'全',58672:'信',58675:'重',58538:'三',58465:'机',58374:'工',58579:'物',58402:'气',58702:'每',58553:'并',58360:'别',58389:'真',58560:'打',58690:'太',58473:'新',58512:'比',58653:'才',58704:'便',58545:'夫',58641:'再',58475:'书',58583:'部',58472:'水',58478:'像',58664:'眼',58586:'等',58568:'体',58674:'却',58490:'加',58476:'电',58346:'主',58630:'界',58595:'门',58502:'利',58713:'海',58587:'受',58548:'听',58351:'表',58547:'德',58443:'少',58460:'克',58636:'代',58585:'员',58625:'许',58694:'稜',58428:'先',58640:'口',58628:'由',58612:'死',58446:'安',58468:'写',58410:'性',58508:'马',58594:'光',58483:'白',58544:'或',58495:'住',58450:'难',58643:'望',58486:'教',58406:'命',58447:'花',58669:'结',58415:'乐',58444:'色',58549:'更',58494:'拉',58409:'东',58658:'神',58557:'记',58602:'处',58559:'让',58610:'母',58513:'父',58500:'应',58378:'直',58680:'字',58352:'场',58383:'平',58454:'报',58671:'友',58668:'关',58452:'放',58627:'至',58400:'张',58455:'认',58416:'接',58552:'告',58614:'入',58582:'笑',58534:'内',58701:'英',58349:'军',58491:'候',58467:'民',58365:'岁',58598:'往',58425:'何',58462:'度',58420:'山',58661:'觉',58615:'路',58648:'带',58470:'万',58377:'男',58520:'边',58646:'风',58600:'解',58431:'叫',58715:'任',58524:'金',58439:'快',58566:'原',58477:'吃',58642:'妈',58437:'变',58411:'通',58451:'师',58395:'立',58369:'象',58706:'数',58705:'四',58379:'失',58567:'满',58373:'战',58448:'远',58659:'格',58434:'士',58679:'音',58432:'轻',58689:'目',58591:'条',58682:'呢'};

const CHAPTERS = [
  {num: 1, title: '第1章 重生冰箱遇毒妇', url: '/reader/7215947883948802575'},
  {num: 2, title: '第2章 融合', url: '/reader/7215948525631996454'},
  {num: 3, title: '第3章 送你们上路', url: '/reader/7216995422726947340'},
  {num: 4, title: '第4章 什么，我成了渡劫境？', url: '/reader/7217255655416496679'},
  {num: 5, title: '第5章 金甲将，你大爷的', url: '/reader/7217794487572791808'},
  {num: 6, title: '第6章 血衣殿', url: '/reader/7218344836423025184'},
  {num: 7, title: '第7章 有钱真好', url: '/reader/7218494080886506042'},
  {num: 8, title: '第8章 好狗胆，我的妹妹也敢动', url: '/reader/7218941548099174923'},
  {num: 9, title: '第9章 护妹狂魔', url: '/reader/7219592801225441796'},
  {num: 10, title: '第10章 来了就不要走了', url: '/reader/7219843463171441186'},
  {num: 11, title: '第11章 武圣武魂真的好弱', url: '/reader/7220417213247783457'},
  {num: 12, title: '第12章 恐怖的火凤', url: '/reader/7220759945636774459'},
  {num: 13, title: '第13章 火星系', url: '/reader/7221279317077000704'},
  {num: 14, title: '第14章 团灭', url: '/reader/7221846416459727363'},
  {num: 15, title: '第15章 你就是狗屁王大少？', url: '/reader/7222180153042928180'},
  {num: 16, title: '第16章 全家修炼', url: '/reader/7222560727968678452'},
  {num: 17, title: '第17章 血二又来了', url: '/reader/7223021441955201547'},
  {num: 18, title: '第18章 血光，你给我滚出来', url: '/reader/7223639331523527220'},
  {num: 19, title: '第19章 血光做的烟花真好看', url: '/reader/7223962109787243041'},
  {num: 20, title: '第20章 黄家千金也被抓来了', url: '/reader/7224758136962613816'},
  {num: 21, title: '第21章 诡异鳞片', url: '/reader/7225195743844237858'},
  {num: 22, title: '第22章 一年后，获得仙法', url: '/reader/7227083145177367072'},
  {num: 23, title: '第23章 我不飞升好不好', url: '/reader/7232467472732029480'},
  {num: 24, title: '第24章 小虎太虎了', url: '/reader/7234119506258297376'},
  {num: 25, title: '第25章 秦家寻仇', url: '/reader/7341210136330895896'},
  {num: 26, title: '第26章 不心软不手软', url: '/reader/7351309028921721406'},
  {num: 27, title: '第27章 清算', url: '/reader/7352468883434897944'},
  {num: 28, title: '第28章 一招，不用手脚', url: '/reader/7355385608807662104'},
  {num: 29, title: '第29章 神秘的女子', url: '/reader/7356053909024014872'},
  {num: 30, title: '第30章 魔修之鳞', url: '/reader/7356416291864855102'},
  {num: 31, title: '第31章 恩公', url: '/reader/7356800482767012414'},
  {num: 32, title: '第32章 交锋', url: '/reader/7356875851863949849'},
  {num: 33, title: '第33章 退敌', url: '/reader/7356952282983842328'},
  {num: 34, title: '第34章 风玉儿', url: '/reader/7357159699642335768'},
  {num: 35, title: '第35章 界面裂缝', url: '/reader/7357249698811363864'},
  {num: 36, title: '第36章 重回灵星', url: '/reader/7357523256691147288'},
  {num: 37, title: '第37章 黑玄令', url: '/reader/7357626172164801048'},
  {num: 38, title: '第38章 隐秘', url: '/reader/7358072757789147672'},
  {num: 39, title: '第39章 灭敌', url: '/reader/7358353189042668057'},
  {num: 40, title: '第40章 黄狮', url: '/reader/7358375709917594137'},
  {num: 41, title: '第41章 灵盟', url: '/reader/7358739011923345945'},
  {num: 42, title: '第42章 回宗，取藕', url: '/reader/7358830604055478809'},
  {num: 43, title: '第43章 塑体成功', url: '/reader/7359388580310958617'},
  {num: 44, title: '第44章 杀进秘境', url: '/reader/7359409043766526489'},
  {num: 45, title: '第45章 大道至尊（全书完）', url: '/reader/7359558411907777049'}
];

const OUTPUT_DIR = join(process.cwd(), 'sources/bingxiang-xiulian/chapters');

async function decryptPage(page) {
  return await page.evaluate((fontMap) => {
    const container = document.querySelector('.muye-reader-content-16') || document.querySelector('[class*="muye-reader-content"]');
    if (!container) return null;
    const ps = container.querySelectorAll('p');
    let result = [];
    for (let p of ps) {
      let text = p.textContent;
      let decoded = '';
      for (let ch of text) {
        let code = ch.charCodeAt(0);
        decoded += fontMap[code] || ch;
      }
      if (decoded.trim()) result.push(decoded);
    }
    return result.join('\n');
  }, FONT_MAP);
}

async function main() {
  mkdirSync(OUTPUT_DIR, { recursive: true });

  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });
  const page = await context.newPage();

  let successCount = 0;
  let failedChapters = [];

  for (const ch of CHAPTERS) {
    const padNum = String(ch.num).padStart(3, '0');
    const filePath = join(OUTPUT_DIR, `${padNum}.md`);
    const url = `https://fanqienovel.com${ch.url}`;

    try {
      console.log(`Fetching ${ch.title}...`);
      await page.goto(url, { waitUntil: 'networkidle', timeout: 30000 });
      // Wait for content to render
      await page.waitForSelector('.muye-reader-content-16, [class*="muye-reader-content"]', { timeout: 10000 });

      const content = await decryptPage(page);
      if (!content || content.length < 50) {
        console.log(`  WARNING: ${ch.title} content too short (${content?.length || 0} chars), retrying...`);
        await page.waitForTimeout(3000);
        const retryContent = await decryptPage(page);
        if (!retryContent || retryContent.length < 50) {
          failedChapters.push(ch);
          console.log(`  FAILED: ${ch.title}`);
          continue;
        }
        writeFileSync(filePath, `# ${ch.title}\n\n${retryContent}\n`, 'utf-8');
      } else {
        writeFileSync(filePath, `# ${ch.title}\n\n${content}\n`, 'utf-8');
      }

      successCount++;
      console.log(`  OK: ${ch.title} (${content?.length || 0} chars)`);

      // Random delay to avoid rate limiting (2-5 seconds)
      const delay = 2000 + Math.random() * 3000;
      await page.waitForTimeout(delay);
    } catch (err) {
      console.log(`  ERROR: ${ch.title} - ${err.message}`);
      failedChapters.push(ch);
      await page.waitForTimeout(5000);
    }
  }

  await browser.close();

  console.log(`\nDone! ${successCount}/${CHAPTERS.length} chapters fetched.`);
  if (failedChapters.length > 0) {
    console.log('Failed chapters:', failedChapters.map(c => c.title).join(', '));
  }
}

main().catch(console.error);
