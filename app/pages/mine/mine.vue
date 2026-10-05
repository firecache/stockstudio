<template>
  <view class="page">
    <view class="card">
      <text class="title">stockstudio</text>
      <text class="muted">v0.1.0 · 移动端 A 股看盘 App</text>
    </view>
    <view class="card">
      <text class="kv-title">数据说明</text>
      <text class="line">日线：腾讯 / 通达信（前复权/不复权，2010 至今）</text>
      <text class="line">分钟：新浪 / 通达信（1/5/15/30/60 分钟）</text>
      <text class="line">分时：腾讯 / 通达信（当日 + 任意历史）</text>
      <text class="line">快照：腾讯 / 通达信（实时）</text>
      <text class="line">图表：K 线 / 分时 / 均线，自研 canvas 渲染</text>
      <text class="line warn">全部真实行情数据，无 mock</text>
    </view>
    <view class="card">
      <text class="kv-title">关于</text>
      <text class="line">仅用于个人学习研究，不构成投资建议。</text>
    </view>
  </view>
</template>

<script>
export default {}
</script>

<style scoped>
.page { padding: 24rpx; }
.card { background: #161b22; border-radius: 16rpx; padding: 32rpx; margin-bottom: 24rpx; }
.title { display: block; font-size: 44rpx; font-weight: 700; margin-bottom: 8rpx; }
.muted { font-size: 24rpx; color: #8b949e; }
.kv-title { display: block; font-size: 30rpx; font-weight: 600; margin-bottom: 16rpx; }
.line { display: block; font-size: 26rpx; color: #e6edf3; padding: 6rpx 0; }
.warn { color: #e64c3c; margin-top: 8rpx; }
</style>
