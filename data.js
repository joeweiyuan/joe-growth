/**
 * 子焘记 · 数据文件
 * 所有统计数据集中于此，首页自动读取，改数据即可更新全站
 */

const SITE_DATA = {
  // ========== 基本档案 ==========
  profile: {
    birthday: '2011.05',
    height: '182.5 cm',
    school: '光华剑桥美高',
    gpa: '3.91',
    toefl: '3.5 / 6.0',
    rowing2k: "7'30\""
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
    // 各年份年度合计（元）
    years: {
      2015: 110000,
      2016: 110000,
      2017: 200000,
      2018: 200000,
      2019: 220000,
      2020: 220000,
      2021: 220000,
      2022: 220000,
      2023: 300000,
      2024: 400000,
      2025: 278400,
      2026: 306261
    },

    /** 计算累计总投入 */
    get total() {
      return Object.values(this.years).reduce((sum, v) => sum + v, 0);
    },

    /** 格式化显示（万元） */
    get display() {
      const wan = Math.floor(this.total / 10000);
      return `¥${wan}万+`;
    }
  }
};
