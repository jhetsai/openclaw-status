import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { TrendingUp, TrendingDown, DollarSign, PieChart as PieChartIcon, Globe, Building2, Sun, Zap } from 'lucide-react'

const COLORS = ['#667eea', '#764ba2', '#f59e0b', '#10b981', '#ef4444', '#3b82f6', '#8b5cf6', '#ec4899', '#06b6d4', '#84cc16', '#f97316']

const R2_BASE = "https://pub-ad498842971c4801a54fabd88ffa4a7f.r2.dev"
const EXCHANGE_RATE = 31.935

function App() {
  const [market, setMarket] = useState('TW')
  const [twStocks, setTwStocks] = useState([])
  const [usStocks, setUsStocks] = useState([])
  const [twHistory, setTwHistory] = useState({})
  const [usHistory, setUsHistory] = useState({})
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('stocks')
  const [updateTime, setUpdateTime] = useState('')
  const [marketStatus, setMarketStatus] = useState({tw: '交易中', us: '交易中'})

  // 讀取資料
  useEffect(() => {
    Promise.all([
      fetch(`${R2_BASE}/taiwan_stocks.json`).then(r => r.json()),
      fetch(`${R2_BASE}/us_stocks.json`).then(r => r.json()),
      fetch(`${R2_BASE}/stock_history.json`).then(r => r.json()),
      fetch(`${R2_BASE}/market_status.json`).then(r => r.json()).catch(() => ({tw:{status:'交易中'}, us:{status:'交易中'}})),
    ]).then(([tw, us, hist, mStatus]) => {
      setMarketStatus({tw: mStatus.tw?.status || '交易中', us: mStatus.us?.status || '交易中'})
      const t = tw[0]?.update_time || ''
      setUpdateTime(t)
      setTwStocks(tw)
      setUsStocks(us || [])
      setTwHistory(hist.tw || {})
      setUsHistory(hist.us || {})
      setSelectedStock(tw[0]?.symbol || null)
      setLoading(false)
    }).catch(err => {
      console.error("載入失敗:", err)
      setLoading(false)
    })
  }, [])

  const stocks = market === 'TW' ? twStocks : usStocks
  const history = market === 'TW' ? twHistory : usHistory

  // 計算統計
  const calculateStats = () => {
    if (!stocks.length) return { totalCost: 0, totalValue: 0, totalGain: 0, gainPct: 0, dailyChange: 0 }
    
    if (market === 'TW') {
      const totalCost = stocks.reduce((sum, s) => sum + (s.total_cost || s.shares * s.cost), 0)
      const totalValue = stocks.reduce((sum, s) => sum + (s.market_value || s.shares * s.price), 0)
      const dailyChange = stocks.reduce((sum, s) => {
        const prev = s.prev_price || s.price
        return sum + (s.price - prev) * s.shares
      }, 0)
      return {
        totalCost, totalValue,
        totalGain: totalValue - totalCost,
        gainPct: ((totalValue - totalCost) / totalCost * 100).toFixed(2),
        dailyChange, dailyPct: (dailyChange / totalValue * 100).toFixed(2)
      }
    } else {
      const totalCost = stocks.reduce((sum, s) => sum + s.shares * s.cost, 0) * EXCHANGE_RATE
      const totalValue = stocks.reduce((sum, s) => sum + s.shares * s.price, 0) * EXCHANGE_RATE
      const dailyChange = stocks.reduce((sum, s) => sum + (s.price - s.prev) * s.shares, 0) * EXCHANGE_RATE
      return {
        totalCost, totalValue,
        totalGain: totalValue - totalCost,
        gainPct: ((totalValue - totalCost) / totalCost * 100).toFixed(2),
        dailyChange, dailyPct: (dailyChange / totalValue * 100).toFixed(2)
      }
    }
  }

  const stats = calculateStats()

  // 走勢圖數據 - 選擇第一支股票的歷史
  const getChartData = () => {
    if (!stocks.length || !selectedStock) return []
    const sym = selectedStock
    const hist = history[sym] || []
    return hist.map(h => ({ date: h.date, price: h.price }))
  }

  const chartData = getChartData()

  // 圓餅圖
  const getPieData = () => {
    return stocks.map((s, i) => ({
      name: s.symbol || s.code,
      value: market === 'TW' 
        ? (s.market_value || s.shares * s.price)
        : (s.shares * s.price * EXCHANGE_RATE),
      color: COLORS[i % COLORS.length]
    }))
  }

  const pieData = getPieData()

  const formatMoney = (num) => {
    if (Math.abs(num) >= 1000000) return (num / 1000000).toFixed(2) + 'M'
    return num.toLocaleString('zh-TW', { maximumFractionDigits: 0 })
  }

  if (loading) {
    return (
      <div style={styles.loading}>
        <div style={styles.loadingText}>📊 載入中...</div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      {/* Header */}
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <h1 style={styles.title}>📊 持股儀表板</h1>
        </div>
        <div style={styles.marketToggle}>
          <button style={{ ...styles.toggleBtn, ...(market === 'TW' ? styles.toggleBtnActive : {}) }} onClick={() => setMarket('TW')}>
            <Building2 size={14} /> 台股<span style={styles.marketStatus}> {marketStatus.tw === '休市中' ? '🔴' : '🟢'}</span>
          </button>
          <button style={{ ...styles.toggleBtn, ...(market === 'US' ? styles.toggleBtnActive : {}) }} onClick={() => setMarket('US')}>
            <Globe size={14} /> 美股<span style={styles.marketStatus}> {marketStatus.us === '休市中' ? '🔴' : '🟢'}</span>
          </button>
        </div>
      </header>



      {/* Nav */}
      <nav style={styles.nav}>
        <span style={{...styles.navBtn, color: '#fff', cursor: 'default', background: 'transparent', border: 'none'}}>📈 持股</span>
      </nav>

      {activeTab === 'stocks' && (
        <>
          {/* Stats */}
          <div style={styles.statsGrid}>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>今日損益</div>
              <div style={{ ...styles.statValue, color: stats.dailyChange >= 0 ? '#22c55e' : '#ef4444' }}>
                {stats.dailyChange >= 0 ? '+' : ''}{formatMoney(stats.dailyChange)}
              </div>
              <div style={{ ...styles.statSub, color: stats.dailyChange >= 0 ? '#22c55e' : '#ef4444' }}>
                {stats.dailyChange >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {Math.abs(stats.dailyPct)}%
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>累計報酬</div>
              <div style={{ ...styles.statValue, color: stats.totalGain >= 0 ? '#22c55e' : '#ef4444' }}>
                {stats.totalGain >= 0 ? '+' : ''}{formatMoney(stats.totalGain)}
              </div>
              <div style={{ ...styles.statSub, color: stats.totalGain >= 0 ? '#22c55e' : '#ef4444' }}>
                {stats.totalGain >= 0 ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {Math.abs(stats.gainPct)}%
              </div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>總市值</div>
              <div style={styles.statValue}>${formatMoney(stats.totalValue)}</div>
              <div style={styles.statSub}><DollarSign size={14} /> {market === 'TW' ? '台幣' : '台幣'}</div>
            </div>
            <div style={styles.statCard}>
              <div style={styles.statLabel}>總成本</div>
              <div style={styles.statValue}>${formatMoney(stats.totalCost)}</div>
              <div style={styles.statSub}><PieChartIcon size={14} /> {stocks.length} 檔股票</div>
            </div>
          </div>

          {/* Charts */}
          <div style={styles.chartsRow}>
            <div style={styles.chartCard}>
              <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'15px'}}>
                <h3 style={styles.chartTitle}>📈 股價走勢圖</h3>
                <select
                  value={selectedStock || ''}
                  onChange={(e) => setSelectedStock(e.target.value)}
                  style={{...styles.stockSelect, color: '#fff', background: '#1a1a2e', border: '1px solid #333'}}
                >
                  {stocks.map(s => (
                    <option key={s.symbol || s.code} value={s.symbol || s.code}>
                      {s.name} ({s.symbol || s.code})
                    </option>
                  ))}
                </select>
              </div>
              <div style={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={200}>
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis dataKey="date" stroke="#666" fontSize={10} tickFormatter={(v) => v?.slice(5)} />
                    <YAxis stroke="#666" fontSize={10} domain={['dataMin', 'dataMax']} tickFormatter={(v) => v?.toFixed(1)} />
                    <Tooltip contentStyle={{ background: '#1d1d1f', border: 'none', borderRadius: 8, color: '#fff' }} labelFormatter={(v) => '日期: ' + v} />
                    <Line type="monotone" dataKey="price" stroke="#667eea" strokeWidth={2} dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div style={styles.chartCard}>
              <h3 style={styles.chartTitle}>📊 持股分布</h3>
              <div style={styles.chartContainer}>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={2} dataKey="value">
                      {pieData.map((entry, index) => <Cell key={index} fill={entry.color} />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: '#1d1d1f', border: 'none', borderRadius: 8, color: '#fff' }} formatter={(v) => formatMoney(v)} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div style={styles.pieLegend}>
                {pieData.slice(0, 5).map((item, i) => (
                  <div key={i} style={styles.legendItem}><span style={{ ...styles.legendDot, background: item.color }}></span>{item.name}</div>
                ))}
              </div>
            </div>
          </div>

          {/* Stock Cards */}
          <div style={styles.stockList}>
            <h3 style={styles.listTitle}>📋 持股明細</h3>
            <div className="stock-cards" style={{display:'grid', gridTemplateColumns:'repeat(auto-fill, minmax(280px, 1fr))', gap:'12px'}}>
              {stocks.map((stock) => {
                const sym = stock.symbol || stock.code
                const gain = market === 'TW'
                  ? (stock.market_value || stock.shares * stock.price) - (stock.total_cost || stock.shares * stock.cost)
                  : ((stock.price - stock.cost) * stock.shares * EXCHANGE_RATE)
                const gainPct = market === 'TW'
                  ? ((stock.market_value || 0) - (stock.total_cost || 0)) / (stock.total_cost || 1) * 100
                  : ((stock.price - stock.cost) / stock.cost * 100)
                return (
                  <div key={sym} style={{...styles.stockCard, background:'linear-gradient(135deg, rgba(102,126,234,0.15) 0%, rgba(118,75,162,0.15) 100%)', borderRadius:'16px', padding:'18px', border:'1px solid rgba(102,126,234,0.3)', boxShadow:'0 4px 12px rgba(0,0,0,0.3)'}}>
                    <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px'}}>
                      <span style={{fontWeight:'700', fontSize:'1.1em', color:'#667eea'}}>{sym}</span>
                      <span style={{fontSize:'0.85em', color:'#aaa', background:'rgba(255,255,255,0.1)', padding:'2px 8px', borderRadius:'4px'}}>{stock.name}</span>
                    </div>
                    <div style={{display:'grid', gridTemplateColumns:'1fr 1fr', gap:'10px', fontSize:'0.9em'}}>
                      <div style={{color:'#888'}}>成本</div><div style={{color:'#fff', fontWeight:'600'}}>{market === 'TW' ? stock.cost : '$' + stock.cost}</div>
                      <div style={{color:'#888'}}>現價</div><div style={{color:'#fff', fontWeight:'600'}}>{market === 'TW' ? stock.price : '$' + stock.price}</div>
                      <div style={{color:'#888'}}>股數</div><div style={{color:'#fff'}}>{stock.shares?.toLocaleString()}</div>
                      <div style={{color:'#888'}}>報酬</div><div style={{color: gain >= 0 ? '#22c55e' : '#ef4444', fontWeight:'700', fontSize:'1em'}}>
                        {gain >= 0 ? '+' : ''}{formatMoney(gain)}
                        <span style={{fontSize:'0.8em'}}> ({gainPct.toFixed(1)}%)</span>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          </div>
        </>
      )}


    </div>
  )
}

const styles = {
  container: { minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%)', color: '#fff', padding: '20px', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif' },
  loading: { minHeight: '100vh', background: 'linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 100%)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '1.5em' },
  loadingText: { opacity: 0.7 },
  header: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', padding: '15px 20px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', backdropFilter: 'blur(10px)' },
  headerLeft: { display: 'flex', alignItems: 'center', gap: '15px' },
  updateTime: { fontSize: '0.75em', color: '#666', fontWeight: '400', marginLeft: '12px' },
  marketStatus: { fontSize: '0.7em', marginLeft: '4px' },
  title: { fontSize: '1.5em', fontWeight: '700', display: 'flex', alignItems: 'center', gap: '10px', margin: 0, color: '#fff' },
  marketToggle: { display: 'flex', gap: '8px', background: 'rgba(255,255,255,0.05)', padding: '4px', borderRadius: '8px' },
  toggleBtn: { display: 'flex', alignItems: 'center', gap: '6px', padding: '8px 16px', border: 'none', borderRadius: '6px', background: 'transparent', color: '#888', cursor: 'pointer', fontSize: '0.9em', fontWeight: '500', transition: 'all 0.2s' },
  toggleBtnActive: { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff' },
  nav: { display: 'flex', gap: '10px', marginBottom: '20px' },
  navBtn: { padding: '10px 20px', border: 'none', borderRadius: '8px', background: 'rgba(255,255,255,0.05)', color: '#888', cursor: 'pointer', fontSize: '0.9em', fontWeight: '500', transition: 'all 0.2s' },
  navBtnActive: { background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: '#fff' },
  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '15px', marginBottom: '20px' },
  statCard: { background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '20px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)' },
  statLabel: { fontSize: '0.85em', color: '#888', marginBottom: '8px' },
  statValue: { fontSize: '1.5em', fontWeight: '700', marginBottom: '5px' },
  statSub: { fontSize: '0.8em', color: '#666', display: 'flex', alignItems: 'center', gap: '5px' },
  chartsRow: { display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '15px', marginBottom: '20px' },
  chartCard: { background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '20px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)' },
  chartTitle: { fontSize: '1em', fontWeight: '600', marginBottom: '15px', color: '#fff' },
  stockSelect: { background: '#1a1a2e', color: '#fff', border: '1px solid rgba(255,255,255,0.2)', borderRadius: '6px', padding: '5px 10px', fontSize: '0.85em', cursor: 'pointer', outline: 'none' },
  chartContainer: { height: '200px' },
  pieLegend: { display: 'flex', flexWrap: 'wrap', gap: '10px', marginTop: '10px', justifyContent: 'center' },
  legendItem: { display: 'flex', alignItems: 'center', gap: '5px', fontSize: '0.8em', color: '#888' },
  legendDot: { width: '10px', height: '10px', borderRadius: '50%' },
  stockList: { background: 'rgba(255,255,255,0.05)', borderRadius: '12px', padding: '20px', backdropFilter: 'blur(10px)', border: '1px solid rgba(255,255,255,0.1)' },
  listTitle: { fontSize: '1em', fontWeight: '600', marginBottom: '15px', color: '#fff' },
  tableHeader: { display: 'flex', padding: '10px 0', borderBottom: '1px solid rgba(255,255,255,0.1)', fontSize: '0.85em', color: '#666', fontWeight: '500' },
  tableRow: { display: 'flex', padding: '12px 0', borderBottom: '1px solid rgba(255,255,255,0.05)', fontSize: '0.9em', alignItems: 'center' },
  otherPanel: { padding: '20px 0' },
  panelTitle: { fontSize: '1.3em', fontWeight: '700', marginBottom: '20px' },
  infoBox: { background: 'rgba(102, 126, 234, 0.1)', borderRadius: '12px', padding: '20px', marginTop: '20px', border: '1px solid rgba(102, 126, 234, 0.3)' },
  infoText: { color: '#667eea', marginBottom: '8px', fontSize: '0.9em' },
}

export default App
