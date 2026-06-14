/**
 * 子焘记 · 数据文件
 * 所有统计数据集中于此，改数据即可更新全站，无须编辑HTML
 * 
 * 如何添加一次新的TOEFL练习：
 *   1. 在 toefl.practiceSessions 数组中加一条记录
 *   2. 如果有错词，加到 errorWords 数组
 *   3. 更新 totalWordsTested 和 totalErrors 计数
 *   ✅ HTML自动更新
 *
 * 如何添加一笔新花销：
 *   1. 在 expenses.years 对象中更新对应年份的数值
 *   2. 同时在 expense-ledger.md 中添加明细记录
 *   ✅ 首页和详情页的总金额自动更新
 */

const SITE_DATA = {
  // ========== 基本档案 ==========
  profile: {
    birthday: '2011.05',
    height: '183 cm',
    school: '光华剑桥美高',
    gpa: '3.91',
    toefl: '3.5 / 6.0',
    toeflTarget: '≥4.5 (6月底)',
    rowing2k: "7'30\" (best)",
    rowing2kLatest: "7'41\" (Jun)",
    rowingTarget: "7'20\" (7.12)",
    offerpath: '🚀 Offer路书',
    offerpathUnis: 119,
    offerpathRecords: 4709,
    offerpathHs: 308
  },

  // ========== 获奖统计 ==========
  awards: {
    total: 38,
    international: 4,
    national: 8,
    provincial: 14,
    school: 6
  },

  // ========== 培养投入 ==========
  expenses: {
    years: {
      // 2018: ¥200,000 + ¥20,000（7月科创）= ¥220,000
      // 2019: ¥220,000 + ¥20,000（7月科创）= ¥240,000
      // 2021: ¥220,000 + ¥20,000（7月科创）= ¥240,000
      // 2022: ¥220,000 + ¥8,000(1月科创) + ¥20,000(7月科创) = ¥248,000
      // 2023: ¥300,000 + ¥8,000(1月科创) + ¥20,000(7月科创) = ¥328,000
      // 2024: ¥400,000 + ¥8,000(1月科创) = ¥408,000
      2015: 110000, 2016: 110000, 2017: 200000, 2018: 220000,
      2019: 240000, 2020: 220000, 2021: 240000, 2022: 248000,
      2023: 328000, 2024: 408000, 2025: 278400, 2026: 306261
    },
    get total() {
      return Object.values(this.years).reduce((sum, v) => sum + v, 0);
    },
    get display() {
      return `¥${Math.floor(this.total / 10000)}万+`;
    }
  },

  // ================================================================
  // 🎯 TOEFL 全部数据
  // ================================================================
  toefl: {
    currentLevel: 3.5,
    targetLevels: [
      { score: 4.5, deadline: '2026-06-30', label: '首考目标' },
      { score: 5.0, deadline: '2026-12-31', label: '年底目标' },
      { score: 5.5, deadline: '2027-06-30', label: '最终目标' }
    ],
    weakAreas: ['口语', '写作'],
    weeklyHours: 6,
    schedule: '周六口写 + 周日听阅',

    /** 全部练习履历——加一条新练习就是在这里加 */
    practiceSessions: [
      {
        date: '2026-05-20', section: '托福阅读 List 1 默写', source: '课堂默写',
        tested: 40, correct: 38, accuracy: 95,
        status: 'warning',
        note: '老师评语：准确率94/100。错词: domesticate↔domestic混淆, abandon↔abandoned混淆。catas-前缀表示"不好的事情"，帮助记忆catastrophic',
        errorWords: [
          { word: 'domesticate', correctMeaning: '驯养，驯化', wrongAnswer: '国内的(domestic)', category: '形近词混淆' },
          { word: 'abandon', correctMeaning: '放弃，遗弃', wrongAnswer: '被抛弃的(abandoned)', category: '形近词混淆' }
        ],
        media: 'assets/images/toefl/list1-dictation.jpg'
      },
      {
        date: '2026-05-22', section: '阅读 List 2 默写', source: '课堂默写',
        tested: 22, correct: 22, accuracy: 100,
        status: 'perfect',
        note: '词汇: exceptional/collect/appeal/array/valid/exploit/unfortunate/err/reformer/approach/verbal/schedule/phenomena/propulsion/inaccurate/bombard/interact/federal/celebrate/attain/incentive/occupy',
        errorWords: [],
        media: 'assets/images/toefl/list2-dictation-100.jpg'
      },
      {
        date: '2026-05-24', section: '酒店话题词汇', source: '默写',
        tested: 27, correct: 27, accuracy: 100,
        status: 'perfect',
        note: 'reservation/check out/front desk/receptionist/single room/amenities/buffet/room service/laundry service/gym/luggage/occupancy/rate/discount/complimentary/lobby/elevator/corridor/balcony/maintenance/air conditioner/lamp/soap/sink/closed/fire alarm/emergency exit',
        errorWords: [],
        media: 'assets/images/toefl/hotel-dictation-full.jpg'
      },
      {
        date: '2026-05-24', section: '人际话题词汇（李晓源）', source: '默写',
        tested: 23, correct: 23, accuracy: 100,
        status: 'perfect',
        note: 'gossiper/praised新增入库',
        errorWords: []
      },
      {
        date: '2026-05-24', section: '人际话题词汇（李思源）', source: '默写',
        tested: 22, correct: 22, accuracy: 100,
        status: 'perfect',
        note: 'neighbour/praised新增入库',
        errorWords: []
      },
      {
        date: '2026-05-24', section: '单词表（List词汇默写）', source: '默写',
        tested: 22, correct: 22, accuracy: 100,
        status: 'perfect',
        note: '22词全部在库，释义准确',
        errorWords: []
      },
      {
        date: '2026-05-24', section: '日程词汇（手写笔记）', source: '默写',
        tested: 21, correct: 21, accuracy: 100,
        status: 'perfect',
        note: '21词全部在库',
        errorWords: []
      },
      {
        date: '2026-06-06', section: '超级学长 List 6', source: '课后词汇表',
        tested: 78, correct: 77, accuracy: 98.7,
        status: 'warning',
        note: '错1词: equable（混淆equal），老师评语准确率99/100',
        errorWords: [{ word: 'equable', correctMeaning: '平稳的，稳定的', wrongAnswer: '相等的(equal)', category: '形近词混淆' }]
      },
      {
        date: '2026-06-06', section: '银行金融话题词汇', source: '课后默写',
        tested: 21, correct: 21, accuracy: 100,
        status: 'perfect',
        note: '老师评语：听力单词默写全部正确 ✅',
        errorWords: []
      },
      {
        date: '2026-06-07', section: '图书馆/学术话题词汇', source: '默写纸',
        tested: 26, correct: 23, accuracy: 88.5,
        status: 'error',
        note: '错3词: procedure/criteria/access · 需重点复习',
        errorWords: [
          { word: 'procedure', correctMeaning: '程序，步骤', category: '拼写不牢' },
          { word: 'criteria', correctMeaning: '标准（复数）', category: '拼写不牢' },
          { word: 'access', correctMeaning: '访问，通道', category: '拼写不牢' }
        ]
      },
      {
        date: '2026-06-07', section: '超级学长 List 7', source: '课后词汇表',
        tested: 77, correct: 77, accuracy: 100,
        status: 'perfect',
        note: '环境/生物/物理学科词汇全覆盖',
        errorWords: []
      },
      {
        date: '2026-06-08', section: '超级学长 补充词汇(List 1补充)', source: '默写纸',
        tested: 22, correct: 22, accuracy: 100,
        status: 'perfect',
        note: 'exceptional/collect/appeal/array/valid/exploit/unfortunate/err/reformer/approach/verbal/schedule/phenomena/propulsion/inaccurate/bombard/interact/federal/celebration/attain/incentive/occupy',
        errorWords: []
      },
      {
        date: '2026-06-08', section: '阅读词汇(List 2延伸)', source: '默写纸',
        tested: 14, correct: 14, accuracy: 100,
        status: 'perfect',
        note: 'vegetable/infant/principal/neighborhood/pinnacle/obligatory/omit/from time to time/anchor/echo/remarkable/ally/visible/domesticate',
        errorWords: []
      },
      {
        date: '2026-06-09', section: '阅读词汇练习(兴趣~认识到)', source: '默写纸',
        tested: 22, correct: 22, accuracy: 100,
        status: 'perfect',
        note: 'interest/investigate/cushion/manual/rendering/underscore/flexible/moral/despite/rupture/saline/executive/respective/isolated/remarkably/foreordain/inspire/sample/obtain/yearning/odd/perceive',
        errorWords: [],
        media: 'assets/images/toefl/list-vocab-1.jpg'
      },
      {
        date: '2026-06-09', section: '超级学长 List 3', source: '课堂词汇表',
        tested: 39, correct: 39, accuracy: 100,
        status: 'perfect',
        note: 'transmit/collapse/ineffectively/incidentally/alarm/criticize/agile/debate/gravitation/magnify/infirm/distract/accompany/attraction/given/eccentric/heir/confirm/advise/ornamentation/endow/malleable/contentious/urbane/focus/paradoxical/functional/opposing/survive/residence/substantial/juncture/description/parallel/delegate/typical/counterpart/bureaucrat/expel',
        errorWords: [],
        media: 'assets/images/toefl/list3-dictation.jpg'
      },
      {
        date: '2026-06-09', section: '听力单词 List 1 默写', source: '课堂默写',
        tested: 27, correct: 27, accuracy: 100,
        status: 'perfect',
        note: '老师评语：全部正确，继续保持～ 词汇涵盖: group project/optional course/intermediate/procedure/equipment/precaution/microscope/field work/expense/tuition/grant/regulation/notification/dorm/stressed out/side effect/immune system/facility/ceremony/appointment/flyer/tough/accessible/career fair/corporation/opportunity/application form',
        errorWords: [],
        media: 'assets/images/toefl/listening-list1-dictation.jpg'
      },
      {
        date: '2026-06-09', section: '阅读 List 30 政府话题默写', source: '课堂默写',
        tested: 100, correct: 98, accuracy: 98,
        status: 'warning',
        note: '老师评语：准确率98/100。政府话题词汇，稍微了解即可。institutionalize由institution(机构)动词化而来，和industrialize由industry变来同理',
        errorWords: [
          { word: 'institutionalize', correctMeaning: '使制度化', category: '词形变化' }
        ]
      },
      {
        date: '2026-06-10', section: '阅读 List 30 政府词汇(二)', source: '默写纸',
        tested: 25, correct: 25, accuracy: 100,
        status: 'perfect',
        note: 'moderate growth/definite market/orientation/adapt to/fluctuation/prosperity/civilian population/rebellion/economic exchange/hereditary/citizenship/auxiliary soldiers/emperor/frontier/pardon/accusation/welfare/patronage/House of Representative/unionization/Monarchy/Industrial Revolution/steam/revolutionary/transform/fuel consumption/manufacturer',
        errorWords: [],
        media: 'assets/images/toefl/list30-dictation-2.jpg'
      },
      {
        date: '2026-06-10', section: '阅读学科词汇 · 政治历史', source: '词汇表自学',
        tested: 75, correct: 75, accuracy: 100,
        status: 'perfect',
        note: '涵盖: 美国政治(共和党/宪法/国会/参议院/修正案等)、古代文明(希腊/罗马/埃及/苏美尔等)、经济贸易(关税/汇票/商人/资本等)',
        errorWords: [],
        media: 'assets/images/toefl/subject-political-history.jpg'
      },
      {
        date: '2026-06-10', section: '听力 List 3 人际话题', source: '课堂默写',
        tested: 26, correct: 20, accuracy: 77,
        status: 'error',
        note: '老师评语：20/26。部分单词元音出现错误，订正之后能够完全背诵正确。词汇: acquaintance/roommate/neighbour/companion/ally/rival/extrovert/hostile/deceitful/generous/honest/untrustworthy/motivate/console/forgive/apologize/negotiate/cooperate/gossip/flatter/overpraised/grateful',
        errorWords: [
          { word: '(元音错误6词)', correctMeaning: '待确认具体词汇', category: '元音拼写' }
        ],
        media: 'assets/images/toefl/listening-list3-dictation.jpg'
      },
      {
        date: '2026-06-11', section: '听力 · 酒店话题词汇(二)', source: '课堂默写',
        tested: 27, correct: 27, accuracy: 100,
        status: 'perfect',
        note: '老师评语：全部正确[强]',
        errorWords: []
      },
      {
        date: '2026-06-11', section: '阅读 List 4 默写', source: '课堂默写',
        tested: 100, correct: 97, accuracy: 97,
        status: 'warning',
        note: '准确率97/100。distinct(形容词: 不同的/明显的)与distinguish(动词: 区分/辨别)混淆——distinct不能当动词用; 试卷图片附后',
        errorWords: [
          { word: 'distinct', correctMeaning: '不同的，明显的', wrongAnswer: '区别于(混为distinguish)', category: '词性混淆' }
        ],
        media: 'assets/images/toefl/list4-97-100.jpg'
      },
      {
        date: '2026-06-12', section: '听力 · 图书馆主题词汇(二)', source: '课堂默写',
        tested: 26, correct: 23, accuracy: 88.5,
        status: 'error',
        note: '老师评语：错误3个，均为单词拼写粗心。词汇: library card/renew/overdue/catalog/database/search engine/journal/article/book reserve/reference book/dictionary/archive/interlibrary loan/printer/scanner/password/troubleshoot/software/cloud storage/citation/quiet',
        errorWords: [
          { word: '(拼写粗心3词)', correctMeaning: '待确认具体词汇', category: '拼写粗心' }
        ],
        media: 'assets/images/toefl/library-dictation-2.jpg'
      },
      {
        date: '2026-06-12', section: '阅读 List 5 默写', source: '课堂默写',
        tested: 100, correct: 99, accuracy: 99,
        status: 'warning',
        note: '老师评语：准确率99/100，很棒！',
        errorWords: [
          { word: '(待确认)', correctMeaning: '待确认具体词汇', category: '待确认' }
        ],
        media: 'assets/images/toefl/list5-99-100.jpg'
      },
      {
        date: '2026-06-07', section: '精听 · TPO1 Conversation D (梦境/图书馆)', source: '精听听写',
        tested: 100, correct: 98, accuracy: 98,
        status: 'warning',
        note: '老师评语：正确率98%[强] 学生与图书管理员关于Dream Interpretation(梦境解读)的文献检索对话。附带中英对照词汇表。错词：assignment写成now(已改)',
        errorWords: [
          { word: 'assignment', correctMeaning: '任务，作业', wrongAnswer: 'now', category: '听辨错误' }
        ],
        media: 'assets/images/toefl/tpo1-conversationD-dictation-20260607.jpg'
      },
      {
        date: '2026-06-14', section: '超级学子 List 29 社会心理词汇', source: '课堂默写',
        tested: 100, correct: 99, accuracy: 99,
        status: 'warning',
        note: '准确率99/100。社会心理学词汇（反思/认知/脑电波/感知/意识等）。错词: perceivable(可感知的)',
        errorWords: [
          { word: 'perceivable', correctMeaning: '可感知的，可认知的', category: '拼写' }
        ],
        media: 'assets/images/toefl/list29-social-psychology-99-100.jpg'
      },
      {
        date: '2026-06-14', section: '词霸 200 We\'re not pressed for time', source: '课堂默写',
        tested: 25, correct: 24, accuracy: 96,
        status: 'warning',
        note: '准确率24/25。学术研究类词汇（提出假设/数据分析/论文撰写/文献引用等）。右侧有questionnaire ×3红笔纠拼，疑似拼写错误',
        errorWords: [
          { word: 'questionnaire', correctMeaning: '问卷，调查表', category: '拼写（待确认）' }
        ],
        media: 'assets/images/toefl/list200-academic-research-24-25.jpg'
      }
    ],

    /** 累计统计（JS自动算，也可手动覆盖） */
    get stats() {
      const s = this.practiceSessions;
      return {
        totalSessions: s.length,
        totalTested: s.reduce((sum, p) => sum + p.tested, 0),
        totalCorrect: s.reduce((sum, p) => sum + p.correct, 0),
        totalErrors: s.reduce((sum, p) => sum + p.errorWords.length, 0),
        accuracyRate: s.length > 0 ? (s.reduce((sum, p) => sum + p.correct, 0) / s.reduce((sum, p) => sum + p.tested, 0) * 100).toFixed(1) : 0,
        wordCompletionPct: Math.round(780 / 6846 * 100)
      };
    },

    /** 所有错词（从练习记录中自动提取） */
    getAllErrorWords() {
      const words = [];
      this.practiceSessions.forEach(session => {
        session.errorWords.forEach(ew => {
          words.push({ ...ew, date: session.date, section: session.section });
        });
      });
      return words;
    },

    /** 词库进度 */
    wordLists: {
      reading: { label: '阅读高频词 List 1~30', total: 30, completed: [1, 2, 3, 4, 5, 6, 7, 30] },
      listening: { label: '听力话题词汇 List 31~49', total: 19, completed: ['银行金融', '图书馆/学术'] },
      subject: { label: '学科分类词汇（35学科）', total: 35, completed: [] },
      phrases: { label: '听力词组 200条', total: 200, completed: [] },
      hfListening: { label: '听力场景高频 118词', total: 118, completed: [] }
    }
  },

  // ================================================================
  // 🚣 赛艇全部数据
  // ================================================================
  rowing: {
    bestTime: "7'30\"",
    bestTimeDate: '2026-02-28',
    latestTime: "7'41\"",
    latestTimeDate: '2026-06-02',
    targets: [
      { time: "7'20\"", deadline: '2026-07-12', label: '泰州集训末测试' },
      { time: '7:10', deadline: '2026-12', label: '年底目标' },
      { time: '7:00', deadline: '2028', label: '巅峰目标·MIT招募标准' }
    ],

    /** 训练和比赛履历 */
    history: [
      { date: '2026-02-28', event: '2km测功仪历史最佳', detail: "7'30\"", status: 'gold' },
      { date: '2026-03', event: '训练出勤', detail: '17天（出勤率55%）', status: 'normal' },
      { date: '2026-04', event: '训练出勤', detail: '15天（出勤率50%）', status: 'normal' },
      { date: '2026-05-16', event: '🥇平湖公开赛500m混双夺冠', detail: '第4→第1 · 0.46秒绝杀 · 人生首赛', status: 'gold' },
      { date: '2026-05-24', event: '室内测功仪2小时训练', detail: '从抗拒到快乐 · 练完满身大汗', status: 'normal' },
      { date: '2026-06-02', event: '⚠️ 2km测功仪', detail: "7'41\" · 比2月倒退11秒", status: 'warning' }
    ],

    /** 当前问题诊断 */
    issues: [
      { problem: '发力顺序不对', detail: '第3段掉速至1\'59"5', severity: 'high' },
      { problem: '体力分配不合理', detail: '前后半程差8.4秒', severity: 'high' },
      { problem: '情绪控制', detail: '急了反而更慢', severity: 'medium' }
    ],

    /** 待办里程碑 */
    milestones: [
      { date: '2026.07.12', label: '🎯 泰州集训末测试', target: "7'20\"", note: '距今天34天 · 封闭集训冲刺' },
      { date: '2026.07.19-08.14', label: '🇺🇸 四所藤校合练', target: '耶鲁·普林斯顿·达特茅斯·宾大', note: '让每个教练记住名字' },
      { date: '2026秋-2027春', label: '⏳ 稳定期', target: '7:10-7:15', note: '积累比赛经验' },
      { date: '2027春', label: '🎯 US Youth Nationals', target: '全国性赛事拿名次', note: '进入招募关注名单' },
      { date: '2028春', label: '💎 巅峰赛季', target: '7:00以内', note: 'MIT招募标准' }
    ]
  },

  // ================================================================
  // 🚀 Offer路书（科创项目）
  // ================================================================
  offerpath: {
    status: '🚀 进行中',
    product: 'Offer路书 — 海外大学录取数据平台',
    url: 'http://43.162.92.9:3000/',
    stats: {
      unis: 119,
      records: 4709,
      hs: 308
    },
    role: {
      title: '产品设计 · 测试 · AI Agent 开发者（Vibe Coding）',
      description: '与爸爸（老板/创始人）一起从0到1打造Offer路书产品',
      contributions: [
        { phase: '产品定位', detail: '参与 Value Proposition 讨论，从用户视角提出产品定位建议' },
        { phase: '产品设计', detail: '参与产品功能设计，与老板一起设计用户体验和交互流程' },
        { phase: '测试', detail: '作为核心内测用户，持续测试产品功能并反馈bug' },
        { phase: 'Bug修复（Vibe Coding）', detail: '通过 AI Agent（Vibe Coding）方式修复产品bug，与老板协作完成代码修改' },
        { phase: '持续迭代', detail: '前期以测试/反馈为主，后期逐步增加编码开发参与度' }
      ],
      skills: ['产品思维', '用户测试', 'AI Agent协作', 'Vibe Coding', '产品设计', 'Bug追踪与修复'],
      vibeCoding: true
    },
    timeline: [
      { date: '2026前期', event: '加入项目', detail: '作为内测用户和产品顾问参与Offer路书' },
      { date: '2026中', event: '功能设计参与', detail: '与老板一起设计产品功能，提供青少年用户视角' },
      { date: '2026中', event: 'Vibe Coding 修复Bug', detail: '通过AI Agent方式参与代码级Bug修复，体验现代AI协作编程' }
    ]
  }
};
