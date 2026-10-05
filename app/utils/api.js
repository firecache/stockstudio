// 后端 API 地址：
// - H5 预览/浏览器：http://127.0.0.1:8000
// - 真机调试：改为电脑局域网 IP（如 http://192.168.x.x:8000）
// - 小程序：需 HTTPS 域名并配置 request 合法域名
const BASE = 'http://127.0.0.1:8000'

function request(path) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: BASE + path,
      timeout: 15000,
      success: (res) => resolve(res.data),
      fail: (err) => reject(err)
    })
  })
}

export function getSymbols() {
  return request('/symbols')
}

export function getKline(code, fq = 'qfq', limit = 300) {
  return request(`/kline/${code}?fq=${fq}&limit=${limit}`)
}

export function getMinute(code, scale = 5) {
  return request(`/minute/${code}?scale=${scale}`)
}

export function getTimeshare(code) {
  return request(`/timeshare/${code}`)
}

export function getQuote(codes) {
  const list = Array.isArray(codes) ? codes.join(',') : codes
  return request(`/quote?codes=${list}`)
}
