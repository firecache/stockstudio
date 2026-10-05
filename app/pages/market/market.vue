<template>
  <view class="page">
    <view class="head">
      <text class="count">{{ list.length }} 只</text>
      <text class="muted">点按进入个股</text>
    </view>
    <scroll-view scroll-y class="list">
      <view
        v-for="s in list"
        :key="s.code"
        class="item"
        @tap="go(s.code)"
      >
        <view class="item-left">
          <text class="name">{{ s.name }}</text>
          <text class="code">{{ s.num }}</text>
        </view>
        <text class="arrow">›</text>
      </view>
    </scroll-view>
  </view>
</template>

<script>
import { getSymbols } from '@/utils/api.js'

export default {
  data() {
    return { list: [] }
  },
  onLoad() {
    this.load()
  },
  methods: {
    async load() {
      try {
        const s = await getSymbols()
        this.list = s.data || []
      } catch (e) {
        uni.showToast({ title: '后端未启动', icon: 'none' })
      }
    },
    go(code) {
      uni.navigateTo({ url: `/pages/stock/stock?code=${code}` })
    }
  }
}
</script>

<style scoped>
.page { padding: 24rpx; }
.head { display: flex; justify-content: space-between; padding: 8rpx 8rpx 24rpx; }
.count { font-size: 28rpx; color: #2f81f7; }
.muted { font-size: 24rpx; color: #8b949e; }
.list { height: calc(100vh - 200rpx); }
.item { display: flex; justify-content: space-between; align-items: center; padding: 24rpx 16rpx; border-bottom: 1rpx solid #30363d; }
.name { font-size: 30rpx; }
.code { font-size: 24rpx; color: #8b949e; margin-left: 16rpx; }
.arrow { color: #8b949e; font-size: 40rpx; }
</style>
