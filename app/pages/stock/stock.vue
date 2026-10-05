<template>
  <view class="page">
    <view v-if="info" class="card">
      <view class="head">
        <text class="name">{{ info.name }}</text>
        <text class="code">{{ info.num }}</text>
      </view>
      <view class="price-row">
        <text class="price" :class="info.up ? 'up' : 'down'">{{ info.close }}</text>
        <text class="chg" :class="info.up ? 'up' : 'down'">
          {{ info.up ? '+' : '' }}{{ info.pct }}%
        </text>
      </view>
      <view class="kv">
        <view class="kv-item"><text class="k">今开</text><text class="v">{{ info.open }}</text></view>
        <view class="kv-item"><text class="k">最高</text><text class="v up">{{ info.high }}</text></view>
        <view class="kv-item"><text class="k">最低</text><text class="v down">{{ info.low }}</text></view>
        <view class="kv-item"><text class="k">成交量(手)</text><text class="v">{{ info.volume }}</text></view>
      </view>
      <text class="muted">日线数据 · {{ info.date }} · 前复权</text>
    </view>

    <view v-if="ts" class="card">
      <text class="card-title">分时（{{ ts.date }}）</text>
      <text class="muted">共 {{ ts.bars }} 个分钟点，均价/成交量待接入图表</text>
      <view class="ts-preview">
        <text class="muted">首点 {{ ts.first }} → 末点 {{ ts.last }}</text>
      </view>
    </view>

    <view class="tip">
      <text class="muted">K 线 / 分时图（klinecharts）为下一阶段接入。</text>
    </view>
  </view>
</template>

<script>
import { getSymbols, getKline, getTimeshare } from '@/utils/api.js'

export default {
  data() {
    return { code: '', info: null, ts: null }
  },
  onLoad(options) {
    this.code = options.code || 'sh600519'
    this.load()
  },
  methods: {
    async load() {
      try {
        // 名称
        const s = await getSymbols()
        const hit = (s.data || []).find((x) => x.code === this.code)
        // 日线
        const k = await getKline(this.code, 'qfq', 2)
        if (k.data && k.data.length >= 2) {
          const last = k.data[k.data.length - 1]
          const prev = k.data[k.data.length - 2]
          const pct = ((last.close - prev.close) / prev.close) * 100
          this.info = {
            name: hit ? hit.name : this.code,
            num: hit ? hit.num : '',
            close: last.close,
            open: last.open,
            high: last.high,
            low: last.low,
            volume: last.volume,
            up: last.close >= prev.close,
            pct: pct.toFixed(2),
            date: last.date
          }
        }
        // 分时
        const t = await getTimeshare(this.code)
        if (t.data && t.data.length) {
          this.ts = {
            date: t.date,
            bars: t.data.length,
            first: t.data[0].time + ' ' + t.data[0].price,
            last: t.data[t.data.length - 1].time + ' ' + t.data[t.data.length - 1].price
          }
        }
      } catch (e) {
        uni.showToast({ title: '后端未启动', icon: 'none' })
      }
    }
  }
}
</script>

<style scoped>
.page { padding: 24rpx; }
.card { background: #161b22; border-radius: 16rpx; padding: 32rpx; margin-bottom: 24rpx; }
.head { display: flex; align-items: baseline; gap: 16rpx; }
.name { font-size: 40rpx; font-weight: 700; }
.code { font-size: 26rpx; color: #8b949e; }
.price-row { display: flex; align-items: baseline; gap: 24rpx; margin-top: 16rpx; }
.price { font-size: 64rpx; font-weight: 700; }
.chg { font-size: 32rpx; }
.up { color: #e64c3c; }
.down { color: #2e9e5b; }
.kv { display: flex; flex-wrap: wrap; margin-top: 24rpx; }
.kv-item { width: 50%; display: flex; justify-content: space-between; padding: 12rpx 0; }
.k { color: #8b949e; font-size: 26rpx; }
.v { font-size: 28rpx; }
.muted { font-size: 24rpx; color: #8b949e; }
.card-title { font-size: 30rpx; font-weight: 600; display: block; margin-bottom: 12rpx; }
.ts-preview { margin-top: 12rpx; }
.tip { margin-top: 8rpx; }
</style>
