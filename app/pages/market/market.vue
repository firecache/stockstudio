<template>
  <view class="page">
    <view class="search">
      <input class="search-input" v-model="kw" placeholder="搜索代码 / 名称" confirm-type="search" @input="onSearch" />
      <text v-if="kw" class="clear" @tap="kw = ''; onSearch()">×</text>
    </view>

    <!-- 搜索结果 -->
    <view v-if="kw" class="list">
      <view v-for="s in results" :key="s.code" class="row">
        <view class="row-left" @tap="open(s.code)">
          <text class="r-name">{{ s.name }}</text>
          <text class="r-code">{{ s.code }} · {{ s.num }}</text>
        </view>
        <text class="r-add" @tap="addWatch(s.code)">＋</text>
      </view>
      <view v-if="!results.length" class="empty"><text class="muted">无匹配结果</text></view>
    </view>

    <!-- 热门列表 -->
    <view v-else class="list">
      <view class="section-title"><text>热门行情</text></view>
      <view v-for="q in quotes" :key="q.code" class="row">
        <view class="row-left" @tap="open(q.code)">
          <text class="r-name">{{ q.name }}</text>
          <text class="r-code">{{ q.code }}</text>
        </view>
        <view class="row-right">
          <text class="r-price" :style="{ color: q.pct >= 0 ? '#e64c3c' : '#2e9e5b' }">{{ fmt(q.price) }}</text>
          <text class="r-pct" :style="{ background: q.pct >= 0 ? '#e64c3c' : '#2e9e5b' }">{{ q.pct >= 0 ? '+' : '' }}{{ q.pct }}%</text>
          <text class="r-add" @tap="addWatch(q.code)">＋</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script>
import { getQuote, getSymbols } from '@/utils/api.js'

const HOT = [
  'sh600519', 'sz000001', 'sz000858', 'sh600036', 'sz002415', 'sh601318', 'sh601398',
  'sh600030', 'sz000333', 'sh600887', 'sz300750', 'sh601012', 'sz002594', 'sh600276',
  'sz000651', 'sh601899', 'sz300059', 'sh600900', 'sz002714', 'sh601088'
]
const KEY = 'stockstudio_watch'

export default {
  data() {
    return { kw: '', quotes: [], results: [], _symbols: null }
  },
  onLoad() {
    this.loadHot()
  },
  methods: {
    fmt(v) {
      return v == null ? '-' : Number(v).toFixed(2)
    },
    async loadHot() {
      try {
        const r = await getQuote(HOT)
        this.quotes = r.data || []
      } catch (e) {
        this.quotes = []
      }
    },
    async onSearch() {
      if (!this.kw.trim()) { this.results = []; return }
      if (!this._symbols) {
        try {
          const r = await getSymbols()
          this._symbols = r.data || []
        } catch (e) {
          this._symbols = []
        }
      }
      const k = this.kw.trim().toLowerCase()
      const name = this.kw.trim()
      this.results = (this._symbols || []).filter(s =>
        String(s.code || '').toLowerCase().includes(k) ||
        String(s.num || '').includes(name) ||
        String(s.name || '').includes(name)
      ).slice(0, 50)
    },
    addWatch(code) {
      const list = uni.getStorageSync(KEY) || []
      if (list.indexOf(code) >= 0) {
        uni.showToast({ title: '已在自选', icon: 'none' })
        return
      }
      list.push(code)
      uni.setStorageSync(KEY, list)
      uni.showToast({ title: '已加入自选', icon: 'success' })
    },
    open(code) {
      uni.navigateTo({ url: '/pages/stock/stock?code=' + code })
    }
  }
}
</script>

<style scoped>
.page { padding: 20rpx; background: #0d1117; min-height: 100vh; }
.search { display: flex; align-items: center; background: #161b22; border-radius: 12rpx; padding: 16rpx 20rpx; margin-bottom: 20rpx; }
.search-input { flex: 1; font-size: 28rpx; color: #e6edf3; }
.clear { color: #8b949e; font-size: 36rpx; padding-left: 16rpx; }
.list { background: #161b22; border-radius: 16rpx; overflow: hidden; }
.section-title { padding: 24rpx 24rpx 8rpx; }
.section-title text { font-size: 28rpx; font-weight: 600; color: #8b949e; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 24rpx; border-bottom: 1rpx solid #21262d; }
.row:last-child { border-bottom: none; }
.row-left { flex: 1; }
.r-name { display: block; font-size: 30rpx; }
.r-code { display: block; font-size: 22rpx; color: #8b949e; margin-top: 4rpx; }
.row-right { display: flex; align-items: center; gap: 16rpx; }
.r-price { font-size: 30rpx; font-weight: 600; }
.r-pct { font-size: 24rpx; color: #fff; padding: 4rpx 12rpx; border-radius: 8rpx; min-width: 100rpx; text-align: center; }
.r-add { font-size: 32rpx; color: #8b949e; padding: 0 8rpx; }
.empty { padding: 60rpx; text-align: center; }
.muted { font-size: 24rpx; color: #8b949e; }
</style>
