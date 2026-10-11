<template>
  <view class="page">
    <!-- 行情头 -->
    <view class="qhead" v-if="q">
      <view class="qhead-top">
        <text class="q-name">{{ q.name }}</text>
        <text class="q-code">{{ code }}</text>
      </view>
      <view class="q-price-row">
        <text class="q-price" :style="{ color: upColor }">{{ fmt(q.price) }}</text>
        <text class="q-pct" :style="{ color: upColor }">{{ pct >= 0 ? '+' : '' }}{{ pct }}%</text>
      </view>
      <view class="q-kv">
        <view class="kv"><text class="k">今开</text><text class="v">{{ fmt(q.open) }}</text></view>
        <view class="kv"><text class="k">最高</text><text class="v" style="color:#e64c3c">{{ fmt(q.high) }}</text></view>
        <view class="kv"><text class="k">最低</text><text class="v" style="color:#2e9e5b">{{ fmt(q.low) }}</text></view>
        <view class="kv"><text class="k">成交量</text><text class="v">{{ fmtVol(q.volume) }}</text></view>
      </view>
    </view>

    <!-- 周期切换 -->
    <view class="tabs">
      <text v-for="t in tabs" :key="t.v" class="tab" :class="{ on: tab === t.v }" @tap="switchTab(t.v)">{{ t.n }}</text>
    </view>

    <!-- 图表 -->
    <view class="chart-wrap">
      <canvas
        canvas-id="stockchart"
        id="stockchart"
        class="chart"
        @touchstart="onTouch"
        @touchmove="onTouch"
        @touchend="onTouchEnd"
      ></canvas>
      <view v-if="!chartReady" class="chart-empty">
        <text class="muted">{{ loading ? '加载中…' : '暂无数据' }}</text>
      </view>
    </view>

    <view class="legend">
      <text v-if="tab !== 'fen'" class="lg"><text class="dot" style="background:#f0b90b"></text>MA5</text>
      <text v-if="tab !== 'fen'" class="lg"><text class="dot" style="background:#2f81f7"></text>MA10</text>
      <text v-if="tab !== 'fen'" class="lg"><text class="dot" style="background:#d96fe0"></text>MA20</text>
      <text v-if="tab === 'fen'" class="lg"><text class="dot" style="background:#2f81f7"></text>价格</text>
      <text v-if="tab === 'fen'" class="lg"><text class="dot" style="background:#f0b90b"></text>均价</text>
    </view>

    <view class="note">
      <text class="muted">数据来自腾讯/新浪/通达信真实行情 · 仅供学习研究，不构成投资建议</text>
    </view>
  </view>
</template>

<script>
import { getKline, getMinute, getTimeshare, getQuote } from '@/utils/api.js'

const UP = '#e64c3c'
const DOWN = '#2e9e5b'

export default {
  data() {
    return {
      code: '',
      q: null,
      pct: 0,
      loading: true,
      chartReady: false,
      tab: 'fen',
      tabs: [
        { v: 'fen', n: '分时' },
        { v: 'day', n: '日K' },
        { v: 'm5', n: '5分' },
        { v: 'm15', n: '15分' },
        { v: 'm30', n: '30分' },
        { v: 'm60', n: '60分' }
      ],
      _bars: [],
      _prevClose: null,
      _cross: null,
      _geom: null
    }
  },
  computed: {
    upColor() {
      return this.pct >= 0 ? UP : DOWN
    }
  },
  onLoad(options) {
    this.code = options.code || 'sh600519'
    this.loadQuote()
    this.switchTab('fen')
  },
  methods: {
    fmt(v) {
      return v == null || v === '' ? '-' : Number(v).toFixed(2)
    },
    fmtVol(v) {
      if (v == null) return '-'
      v = Number(v)
      if (v >= 1e8) return (v / 1e8).toFixed(2) + '亿'
      if (v >= 1e4) return (v / 1e4).toFixed(2) + '万'
      return String(Math.round(v))
    },
    async loadQuote() {
      try {
        const r = await getQuote(this.code)
        const d = (r.data && r.data[0]) || null
        if (d) {
          this.q = d
          this.pct = d.pct != null ? d.pct : 0
          if (d.prev_close != null) this._prevClose = d.prev_close
        }
      } catch (e) {
        // 图表仍可用本地落盘数据
      }
    },
    async switchTab(t) {
      this.tab = t
      this.loading = true
      this.chartReady = false
      this._cross = null
      try {
        if (t === 'fen') {
          const r = await getTimeshare(this.code)
          this._bars = (r.data || []).map(p => {
            let avg = p.average != null ? p.average : null
            if (avg == null && p.cum_volume) {
              avg = p.cum_amount != null ? p.cum_amount / (p.cum_volume * 100) : null
            }
            return { ...p, average: avg }
          })
          if (!this._prevClose && this._bars.length > 0) {
            this._prevClose = this._bars[0].price
          }
        } else if (t === 'day') {
          const r = await getKline(this.code, 'qfq', 250)
          this._bars = r.data || []
          if (this._bars.length >= 2 && !this._prevClose) {
            this._prevClose = this._bars[this._bars.length - 2].close
          }
        } else {
          const scale = { m5: 5, m15: 15, m30: 30, m60: 60 }[t]
          const r = await getMinute(this.code, scale)
          this._bars = r.data || []
        }
      } catch (e) {
        this._bars = []
      }
      this.loading = false
      this.chartReady = this._bars.length > 0
      this.$nextTick(() => this.draw())
    },
    getCanvas() {
      return new Promise((resolve) => {
        uni.createSelectorQuery().in(this).select('#stockchart').boundingClientRect(rect => {
          resolve({ w: rect ? rect.width : 0, h: rect ? rect.height : 0 })
        }).exec()
      })
    },
    async draw() {
      const { w, h } = await this.getCanvas()
      if (!w || !h || !this._bars.length) return
      const ctx = uni.createCanvasContext('stockchart', this)
      if (this.tab === 'fen') {
        this.drawFen(ctx, w, h)
      } else {
        this.drawKline(ctx, w, h)
      }
      if (this._cross != null) {
        this.drawCross(ctx, w, h)
      }
      ctx.draw()
    },
    layout(w, h) {
      const padL = 4, padR = 54, padT = 10, padB = 20
      const volH = h * 0.22
      const mainH = h - padT - padB - volH
      const n = this._bars.length
      const cw = (w - padL - padR) / Math.max(1, n)
      return { w, h, padL, padR, padT, padB, volH, mainH, n, cw }
    },
    drawKline(ctx, w, h) {
      const bars = this._bars
      const g = this.layout(w, h)
      const { padL, padR, padT, padB, volH, mainH, n, cw } = g
      let hi = -Infinity, lo = Infinity
      for (const b of bars) {
        if (b.high > hi) hi = b.high
        if (b.low < lo) lo = b.low
      }
      if (!isFinite(hi) || hi === lo) { hi = (hi || 10) + 0.5; lo = (lo || 10) - 0.5 }
      const range = hi - lo
      const x = i => padL + cw * (i + 0.5)
      const y = p => padT + (hi - p) / range * mainH
      this._geom = { ...g, hi, lo, range, x, y }
      // 网格 + 价格标签
      ctx.setStrokeStyle('#21262d'); ctx.setLineWidth(1)
      ctx.setFillStyle('#8b949e'); ctx.setFontSize(10)
      for (let k = 0; k <= 4; k++) {
        const p = hi - range * k / 4
        const yy = y(p)
        ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke()
        ctx.setTextAlign('left'); ctx.fillText(p.toFixed(2), w - padR + 4, yy - 5)
      }
      // 成交量 + 蜡烛
      let vmax = 0
      for (const b of bars) if (b.volume > vmax) vmax = b.volume
      for (let i = 0; i < n; i++) {
        const b = bars[i]
        const up = b.close >= b.open
        const color = up ? UP : DOWN
        const cx = x(i)
        const bodyW = Math.max(1, cw * 0.6)
        // 影线
        ctx.setStrokeStyle(color); ctx.setLineWidth(1)
        ctx.beginPath(); ctx.moveTo(cx, y(b.high)); ctx.lineTo(cx, y(b.low)); ctx.stroke()
        // 实体
        const yo = y(b.open), yc = y(b.close)
        ctx.setFillStyle(color)
        ctx.fillRect(cx - bodyW / 2, Math.min(yo, yc), bodyW, Math.max(1, Math.abs(yo - yc)))
        // 量
        const vh = vmax ? b.volume / vmax * volH : 0
        ctx.setFillStyle(color)
        ctx.fillRect(cx - bodyW / 2, h - padB - vh, bodyW, vh)
      }
      // MA
      const ma = this.computeMA(bars)
      const maCfg = [[5, '#f0b90b'], [10, '#2f81f7'], [20, '#d96fe0']]
      for (const [p, color] of maCfg) {
        const arr = ma[p]
        if (!arr) continue
        ctx.setStrokeStyle(color); ctx.setLineWidth(1)
        ctx.beginPath()
        let started = false
        for (let i = 0; i < n; i++) {
          const v = arr[i]
          if (v == null) { started = false; continue }
          if (!started) { ctx.moveTo(x(i), y(v)); started = true }
          else ctx.lineTo(x(i), y(v))
        }
        ctx.stroke()
      }
      // 日期
      ctx.setFillStyle('#8b949e'); ctx.setFontSize(10); ctx.setTextAlign('center')
      const step = Math.ceil(n / 5)
      for (let i = 0; i < n; i += step) {
        ctx.fillText(this.xLabel(bars[i]), x(i), h - 6)
      }
    },
    drawFen(ctx, w, h) {
      const rows = this._bars
      const g = this.layout(w, h)
      const { padL, padR, padT, padB, volH, mainH, n, cw } = g
      let hi = -Infinity, lo = Infinity
      for (const r of rows) {
        if (r.price > hi) hi = r.price
        if (r.price < lo) lo = r.price
      }
      const pc = this._prevClose
      if (pc != null) { hi = Math.max(hi, pc); lo = Math.min(lo, pc) }
      if (!isFinite(hi) || hi === lo) { hi = (hi || 10) + 0.01; lo = (lo || 10) - 0.01 }
      const range = hi - lo
      const x = i => padL + cw * (i + 0.5)
      const y = p => padT + (hi - p) / range * mainH
      this._geom = { ...g, hi, lo, range, x, y }
      // 网格
      ctx.setStrokeStyle('#21262d'); ctx.setLineWidth(1)
      ctx.setFillStyle('#8b949e'); ctx.setFontSize(10)
      for (let k = 0; k <= 4; k++) {
        const p = hi - range * k / 4
        const yy = y(p)
        ctx.beginPath(); ctx.moveTo(padL, yy); ctx.lineTo(w - padR, yy); ctx.stroke()
        ctx.setTextAlign('left'); ctx.fillText(p.toFixed(2), w - padR + 4, yy - 5)
      }
      // 昨收虚线
      if (pc != null) {
        const yy = y(pc)
        ctx.setStrokeStyle('#8b949e'); ctx.setLineWidth(1)
        ctx.beginPath()
        for (let xx = padL; xx < w - padR; xx += 6) { ctx.moveTo(xx, yy); ctx.lineTo(xx + 3, yy) }
        ctx.stroke()
      }
      // 分时价格线
      ctx.setStrokeStyle('#2f81f7'); ctx.setLineWidth(1.2)
      ctx.beginPath()
      for (let i = 0; i < n; i++) {
        const xx = x(i), yy = y(rows[i].price)
        if (i === 0) ctx.moveTo(xx, yy); else ctx.lineTo(xx, yy)
      }
      ctx.stroke()
      // 均价线
      ctx.setStrokeStyle('#f0b90b'); ctx.setLineWidth(1)
      ctx.beginPath()
      let started = false
      for (let i = 0; i < n; i++) {
        const a = rows[i].average
        if (a == null) { started = false; continue }
        const xx = x(i), yy = y(a)
        if (!started) { ctx.moveTo(xx, yy); started = true }
        else ctx.lineTo(xx, yy)
      }
      ctx.stroke()
      // 量
      let vmax = 0
      for (const r of rows) { const v = r.volume || 0; if (v > vmax) vmax = v }
      for (let i = 0; i < n; i++) {
        const r = rows[i], v = r.volume || 0
        const vh = vmax ? v / vmax * volH : 0
        ctx.setFillStyle('#3a4250')
        ctx.fillRect(x(i) - Math.max(1, cw * 0.35), h - padB - vh, Math.max(1, cw * 0.7), vh)
      }
      // 时间轴
      ctx.setFillStyle('#8b949e'); ctx.setFontSize(10); ctx.setTextAlign('center')
      const step = Math.ceil(n / 4)
      for (let i = 0; i < n; i += step) {
        const t = String(rows[i].time || '')
        ctx.fillText(t.length >= 4 ? t.slice(0, 2) + ':' + t.slice(2, 4) : t, x(i), h - 6)
      }
    },
    computeMA(bars) {
      const out = { 5: [], 10: [], 20: [] }
      for (const p of [5, 10, 20]) {
        let sum = 0
        for (let i = 0; i < bars.length; i++) {
          sum += bars[i].close
          if (i >= p) sum -= bars[i - p].close
          out[p].push(i >= p - 1 ? sum / p : null)
        }
      }
      return out
    },
    xLabel(b) {
      const s = String((b && (b.date || b.datetime)) || '')
      if (s.includes(' ')) return s.slice(11, 16)
      if (s.length >= 10) return s.slice(2, 10)
      if (s.length >= 8) return s.slice(2, 8)
      return s
    },
    drawCross(ctx, w, h) {
      const g = this._geom
      if (!g || this._cross == null) return
      const i = this._cross
      const b = this._bars[i]
      if (!b) return
      const cx = g.x(i)
      ctx.setStrokeStyle('#8b949e'); ctx.setLineWidth(1)
      ctx.beginPath(); ctx.moveTo(cx, g.padT); ctx.lineTo(cx, h - g.padB); ctx.stroke()
      const price = b.price != null ? b.price : b.close
      const yy = g.y(price != null ? price : 0)
      ctx.beginPath(); ctx.moveTo(g.padL, yy); ctx.lineTo(w - g.padR, yy); ctx.stroke()
      // 信息框
      const label = this.tab === 'fen'
        ? (String(b.time || '') + '  ' + (price != null ? Number(price).toFixed(2) : ''))
        : (String(b.date || b.datetime || '') + '  O' + this.fmt(b.open) + ' H' + this.fmt(b.high) + ' L' + this.fmt(b.low) + ' C' + this.fmt(b.close))
      ctx.setFillStyle('rgba(13,17,23,0.92)')
      ctx.fillRect(6, 6, Math.min(200, w - 12), 20)
      ctx.setFillStyle('#e6edf3'); ctx.setFontSize(10); ctx.setTextAlign('left')
      ctx.fillText(label, 10, 20)
    },
    onTouch(e) {
      if (!this._geom || !this._bars.length) return
      const t = e.touches && e.touches[0]
      if (!t) return
      const g = this._geom
      const idx = Math.round((t.x - g.padL) / g.cw - 0.5)
      this._cross = Math.max(0, Math.min(g.n - 1, idx))
      this.draw()
    },
    onTouchEnd() {
      this._cross = null
      this.draw()
    }
  }
}
</script>

<style scoped>
.page { padding: 20rpx; background: #0d1117; min-height: 100vh; }
.qhead { background: #161b22; border-radius: 16rpx; padding: 28rpx; margin-bottom: 20rpx; }
.qhead-top { display: flex; align-items: baseline; gap: 16rpx; }
.q-name { font-size: 38rpx; font-weight: 700; }
.q-code { font-size: 24rpx; color: #8b949e; }
.q-price-row { display: flex; align-items: baseline; gap: 20rpx; margin-top: 12rpx; }
.q-price { font-size: 60rpx; font-weight: 700; }
.q-pct { font-size: 30rpx; }
.q-kv { display: flex; flex-wrap: wrap; margin-top: 20rpx; }
.kv { width: 50%; display: flex; justify-content: space-between; padding: 8rpx 0; }
.k { color: #8b949e; font-size: 24rpx; }
.v { font-size: 26rpx; }
.tabs { display: flex; background: #161b22; border-radius: 12rpx; padding: 8rpx; margin-bottom: 20rpx; }
.tab { flex: 1; text-align: center; font-size: 26rpx; color: #8b949e; padding: 10rpx 0; border-radius: 8rpx; }
.tab.on { background: #2f81f7; color: #fff; font-weight: 600; }
.chart-wrap { position: relative; background: #161b22; border-radius: 16rpx; padding: 12rpx; }
.chart { width: 100%; height: 660rpx; }
.chart-empty { position: absolute; left: 0; right: 0; top: 0; bottom: 0; display: flex; align-items: center; justify-content: center; }
.legend { display: flex; gap: 24rpx; padding: 16rpx 8rpx; }
.lg { display: flex; align-items: center; gap: 8rpx; font-size: 22rpx; color: #8b949e; }
.dot { width: 14rpx; height: 14rpx; border-radius: 50%; }
.note { padding: 20rpx 8rpx; }
.muted { font-size: 22rpx; color: #8b949e; }
</style>
