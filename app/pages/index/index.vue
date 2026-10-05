<template>
  <view class="page">
    <view class="hero">
      <text class="title">stockstudio</text>
      <text class="sub">真实 A 股行情 · 数据无 mock</text>
    </view>

    <view class="stat" v-if="symbolCount">
      <text class="stat-num">{{ symbolCount }}</text>
      <text class="stat-label">只 A 股已接入</text>
    </view>

    <view class="card" v-if="maotai">
      <view class="card-head">
        <text class="card-title">贵州茅台</text>
        <text class="card-code">600519</text>
      </view>
      <view class="row">
        <text class="price" :class="maotai.up ? 'up' : 'down'">{{ maotai.close }}</text>
        <text class="change" :class="maotai.up ? 'up' : 'down'">
          {{ maotai.up ? '+' : '' }}{{ maotai.pct }}%
        </text>
      </view>
      <text class="muted">最新收盘 · {{ maotai.date }}</text>
    </view>

    <view class="tip">
      <text class="muted">数据来自腾讯/新浪免费行情源，真实落盘 Parquet 后经 API 返回。</text>
    </view>
  </view>
</template>

<script>
import { getSymbols, getKline } from '@/utils/api.js'

export default {
  data() {
    return { symbolCount: 0, maotai: null }
  },
  onLoad() {
    this.load()
  },
  methods: {
    async load() {
      try {
        const s = await getSymbols()
        this.symbolCount = s.count
        const k = await getKline('sh600519', 'qfq', 2)
        if (k.data && k.data.length >= 2) {
          const last = k.data[k.data.length - 1]
          const prev = k.data[k.data.length - 2]
          const pct = ((last.close - prev.close) / prev.close) * 100
          this.maotai = {
            close: last.close,
            up: last.close >= prev.close,
            pct: pct.toFixed(2),
            date: last.date
          }
        }
      } catch (e) {
        console.error(e)
        uni.showToast({ title: '后端未启动，请运行 backend/server.py', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
.page { padding: 40rpx; }
.hero { margin-bottom: 48rpx; }
.title { display: block; font-size: 56rpx; font-weight: 700; }
.sub { display: block; font-size: 26rpx; color: #8b949e; margin-top: 8rpx; }
.stat { display: flex; flex-direction: column; align-items: center; padding: 40rpx; background: #161b22; border-radius: 16rpx; margin-bottom: 24rpx; }
.stat-num { font-size: 64rpx; font-weight: 700; color: #2f81f7; }
.stat-label { font-size: 24rpx; color: #8b949e; margin-top: 8rpx; }
.card { background: #161b22; border-radius: 16rpx; padding: 32rpx; }
.card-head { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 34rpx; font-weight: 600; }
.card-code { font-size: 24rpx; color: #8b949e; }
.row { display: flex; align-items: baseline; gap: 24rpx; margin-top: 16rpx; }
.price { font-size: 56rpx; font-weight: 700; }
.change { font-size: 30rpx; }
.up { color: #e64c3c; }
.down { color: #2e9e5b; }
.muted { font-size: 24rpx; color: #8b949e; }
.tip { margin-top: 32rpx; }
</style>
