<template>
  <view class="page">
    <!-- 搜索框 -->
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

    <!-- 全市场列表 -->
    <template v-else>
      <!-- 排序 tab -->
      <view class="sortbar">
        <text v-for="s in sorts" :key="s.v" class="sort" :class="{ on: sort === s.v }" @tap="switchSort(s.v)">{{ s.n }}</text>
      </view>
      <!-- 列表头 -->
      <view class="list-head">
        <text class="h-name">名称</text>
        <text class="h-price">最新价</text>
        <text class="h-pct">涨跌幅</text>
      </view>
      <!-- 股票列表 -->
      <view class="list">
        <view v-for="q in visibleQuotes" :key="q.code" class="row">
          <view class="row-left" @tap="open(q.code)">
            <text class="r-name">{{ q.name }}</text>
            <text class="r-code">{{ q.code }}</text>
          </view>
          <view class="row-right">
            <text class="r-price" :style="{ color: colorOf(q.pct) }">{{ fmt(q.price) }}</text>
            <text class="r-pct" :style="{ background: colorOf(q.pct) }">{{ pctText(q.pct) }}</text>
            <text class="r-add" @tap="addWatch(q.code)">＋</text>
          </view>
        </view>
        <view v-if="loading" class="loading"><text class="muted">加载中…</text></view>
        <view v-else-if="visibleCount >= allQuotes.length" class="loading"><text class="muted">已加载全部 {{ allQuotes.length }} 只</text></view>
      </view>
    </template>
  </view>
</template>

<script>
import { getMarket, getSymbols } from '@/utils/api.js'

const KEY = 'stockstudio_watch'
const PAGE_SIZE = 50

export default {
  data() {
    return {
      kw: '',
      results: [],
      _symbols: null,
      allQuotes: [],
      visibleCount: PAGE_SIZE,
      sort: 'pct',
      sorts: [
        { v: 'pct', n: '涨跌幅' },
        { v: 'amount', n: '成交额' },
        { v: 'turnover', n: '换手率' },
        { v: 'price', n: '最新价' }
      ],
      loading: false,
      loaded: false
    }
  },
  computed: {
    visibleQuotes() {
      return this.allQuotes.slice(0, this.visibleCount)
    }
  },
  onLoad() {
    this.loadMarket()
  },
  onReachBottom() {
    if (this.kw) return
    if (this.visibleCount < this.allQuotes.length) {
      this.visibleCount += PAGE_SIZE
    }
  },
  methods: {
    fmt(v) {
      return v == null ? '-' : Number(v).toFixed(2)
    },
    pctText(v) {
      return v == null ? '-' : (v >= 0 ? '+' : '') + v + '%'
    },
    colorOf(v) {
      if (v == null) return '#8b949e'
      return v >= 0 ? '#e64c3c' : '#2e9e5b'
    },
    async loadMarket() {
      this.loading = true
      try {
        const r = await getMarket()
        this.allQuotes = r.data || []
        this.visibleCount = Math.min(PAGE_SIZE, this.allQuotes.length)
        this.loaded = true
      } catch (e) {
        this.allQuotes = []
      }
      this.loading = false
    },
    switchSort(s) {
      if (this.sort === s) return
      this.sort = s
      this.sortAll()
    },
    sortAll() {
      const key = this.sort
      this.allQuotes = [...this.allQuotes].sort((a, b) => {
        const va = a[key], vb = b[key]
        const na = va == null, nb = vb == null
        if (na && nb) return 0
        if (na) return 1
        if (nb) return -1
        return vb - va
      })
      this.visibleCount = Math.min(PAGE_SIZE, this.allQuotes.length)
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
.sortbar { display: flex; background: #161b22; border-radius: 12rpx; padding: 8rpx; margin-bottom: 12rpx; }
.sort { flex: 1; text-align: center; font-size: 26rpx; color: #8b949e; padding: 10rpx 0; border-radius: 8rpx; }
.sort.on { background: #2f81f7; color: #fff; font-weight: 600; }
.list-head { display: flex; justify-content: space-between; padding: 12rpx 24rpx 8rpx; font-size: 22rpx; color: #8b949e; }
.h-name { flex: 1; }
.h-price { width: 140rpx; text-align: right; }
.h-pct { width: 130rpx; text-align: right; }
.list { background: #161b22; border-radius: 16rpx; overflow: hidden; }
.section-title { padding: 24rpx 24rpx 8rpx; }
.section-title text { font-size: 28rpx; font-weight: 600; color: #8b949e; }
.row { display: flex; align-items: center; justify-content: space-between; padding: 24rpx; border-bottom: 1rpx solid #21262d; }
.row:last-child { border-bottom: none; }
.row-left { flex: 1; }
.r-name { display: block; font-size: 30rpx; }
.r-code { display: block; font-size: 22rpx; color: #8b949e; margin-top: 4rpx; }
.row-right { display: flex; align-items: center; gap: 16rpx; }
.r-price { font-size: 30rpx; font-weight: 600; min-width: 140rpx; text-align: right; }
.r-pct { font-size: 24rpx; color: #fff; padding: 4rpx 12rpx; border-radius: 8rpx; min-width: 130rpx; text-align: center; }
.r-add { font-size: 32rpx; color: #8b949e; padding: 0 8rpx; }
.loading { padding: 20rpx; text-align: center; }
.empty { padding: 60rpx; text-align: center; }
.muted { font-size: 24rpx; color: #8b949e; }
</style>
