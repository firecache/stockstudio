<template>
  <view class="page">
    <view class="header">
      <text class="app-name">stockstudio</text>
      <text class="slogan">移动端 A 股看盘</text>
    </view>

    <!-- 自选股 -->
    <view class="card">
      <view class="card-head">
        <text class="card-title">自选股</text>
        <text class="add" @tap="goMarket">＋ 添加</text>
      </view>
      <view v-if="!quotes.length" class="empty">
        <text class="muted">暂无自选，去行情页搜索添加。</text>
      </view>
      <view v-for="q in quotes" :key="q.code" class="row">
        <view class="row-left" @tap="open(q.code)">
          <text class="r-name">{{ q.name }}</text>
          <text class="r-code">{{ q.code }}</text>
        </view>
        <view class="row-right">
          <text class="r-price" :style="{ color: (q.pct == null || q.pct >= 0) ? '#e64c3c' : '#2e9e5b' }">{{ fmt(q.price) }}</text>
          <text class="r-pct" :style="{ background: (q.pct == null || q.pct >= 0) ? '#e64c3c' : '#2e9e5b' }">{{ q.pct == null ? '-' : (q.pct >= 0 ? '+' : '') + q.pct + '%' }}</text>
          <text class="r-del" @tap="remove(q.code)">✕</text>
        </view>
      </view>
    </view>

    <!-- 快捷入口 -->
    <view class="card">
      <text class="card-title">快捷入口</text>
      <view class="entry" @tap="goMarket"><text>行情 · 搜索</text><text class="arrow">›</text></view>
      <view class="entry" @tap="open('sh600519')"><text>贵州茅台</text><text class="arrow">›</text></view>
      <view class="entry" @tap="open('sh000001')"><text>上证指数（示例）</text><text class="arrow">›</text></view>
    </view>
  </view>
</template>

<script>
import { getQuote } from '@/utils/api.js'

const DEFAULT_WATCH = ['sh600519', 'sz000001', 'sh601398', 'sz300750', 'sh600036']
const KEY = 'stockstudio_watch'

export default {
  data() {
    return { watch: [], quotes: [] }
  },
  onShow() {
    this.watch = uni.getStorageSync(KEY) || DEFAULT_WATCH
    this.refresh()
  },
  methods: {
    fmt(v) {
      return v == null ? '-' : Number(v).toFixed(2)
    },
    async refresh() {
      if (!this.watch.length) { this.quotes = []; return }
      try {
        const r = await getQuote(this.watch)
        const map = {}
        for (const q of (r.data || [])) map[q.code] = q
        this.quotes = this.watch.map(c => map[c] || { code: c, name: c, price: null, pct: null })
      } catch (e) {
        this.quotes = []
      }
    },
    remove(code) {
      this.watch = this.watch.filter(c => c !== code)
      uni.setStorageSync(KEY, this.watch)
      this.refresh()
    },
    open(code) {
      uni.navigateTo({ url: '/pages/stock/stock?code=' + code })
    },
    goMarket() {
      uni.switchTab({ url: '/pages/market/market' })
    }
  }
}
</script>

<style scoped>
.page { padding: 20rpx; background: #0d1117; min-height: 100vh; }
.header { padding: 24rpx 8rpx 32rpx; }
.app-name { display: block; font-size: 48rpx; font-weight: 700; }
.slogan { font-size: 26rpx; color: #8b949e; }
.card { background: #161b22; border-radius: 16rpx; padding: 28rpx; margin-bottom: 24rpx; }
.card-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8rpx; }
.card-title { font-size: 30rpx; font-weight: 600; }
.add { font-size: 24rpx; color: #2f81f7; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 20rpx 0; border-bottom: 1rpx solid #21262d; }
.row:last-child { border-bottom: none; }
.row-left { flex: 1; }
.r-name { display: block; font-size: 30rpx; }
.r-code { display: block; font-size: 22rpx; color: #8b949e; margin-top: 4rpx; }
.row-right { display: flex; align-items: center; gap: 16rpx; }
.r-price { font-size: 30rpx; font-weight: 600; }
.r-pct { font-size: 24rpx; color: #fff; padding: 4rpx 12rpx; border-radius: 8rpx; min-width: 100rpx; text-align: center; }
.r-del { font-size: 26rpx; color: #8b949e; padding: 0 8rpx; }
.empty { padding: 40rpx 0; text-align: center; }
.muted { font-size: 24rpx; color: #8b949e; }
.entry { display: flex; justify-content: space-between; align-items: center; padding: 20rpx 0; }
.arrow { color: #8b949e; font-size: 32rpx; }
</style>
