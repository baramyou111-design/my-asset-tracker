import streamlit as st
import yfinance as yf
import pandas as pd

# ==========================================
# 1. ตั้งค่าหน้าจอ Dashboard
# ==========================================
st.set_page_config(page_title="Global Asset Tracker", layout="wide", page_icon="🌍")
st.title("🌍 Global Asset Tracker & Daily Buy Signals")
st.markdown("ระบบวิเคราะห์แนวโน้มและแนะนำจุดเข้าซื้อสำหรับ **หุ้นไทย, หุ้นต่างประเทศ และ คริปโตเคอร์เรนซี**")

# ==========================================
# 2. เมนูด้านข้าง (Sidebar) สำหรับตั้งค่าและอัปโหลด
# ==========================================
st.sidebar.header("⚙️ 1. การตั้งค่าสัญลักษณ์ (Ticker)")
ticker_mode = st.sidebar.radio(
    "รูปแบบสัญลักษณ์ในไฟล์ของคุณ:",
    options=[
        "ผสม (ต้องใส่สัญลักษณ์ให้ตรงเป๊ะ)", 
        "หุ้นไทยล้วน (ระบบจะเติม .BK ให้อัตโนมัติ)"
    ],
    help="ถ้าเลือก 'ผสม' คุณต้องพิมพ์สัญลักษณ์ตาม Yahoo Finance เช่น หุ้นไทย=PTT.BK, หุ้นอเมริกา=AAPL, คริปโต=BTC-USD"
)

st.sidebar.header("📂 2. อัปโหลดไฟล์ Track set")
uploaded_file = st.sidebar.file_uploader("ลากไฟล์ Track set ของคุณมาวางที่นี่", type=["csv", "xlsx"])

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith('.csv'):
            df_track = pd.read_csv(uploaded_file, header=None)
        else:
            df_track = pd.read_excel(uploaded_file, header=None)
        
        raw_tickers = df_track[0].dropna().astype(str).tolist()
        
        # จัดการรูปแบบชื่อ Ticker ตามโหมดที่เลือก
        tickers = []
        for t in raw_tickers:
            t = t.strip().upper()
            if t and t not in ["ชื่อหุ้น", "TICKER", "SYMBOL"]:
                if ticker_mode == "หุ้นไทยล้วน (ระบบจะเติม .BK ให้อัตโนมัติ)":
                    if not t.endswith('.BK'):
                        t += '.BK'
                tickers.append(t)
                
        st.sidebar.success(f"✅ โหลดสัญลักษณ์สำเร็จ {len(tickers)} รายการ")
        
    except Exception as e:
        st.sidebar.error("เกิดข้อผิดพลาดในการอ่านไฟล์ โปรดตรวจสอบรูปแบบไฟล์ของคุณ")
        tickers = []

    # ==========================================
    # 3. ระบบประมวลผลสัญญาณซื้อขาย (Trading Logic)
    # ==========================================
    if len(tickers) > 0 and st.sidebar.button("🔍 เริ่มสแกนหาสัญญาณเข้าซื้อ"):
        with st.spinner("กำลังดึงข้อมูลจากตลาดทั่วโลกและคำนวณสัญญาณ..."):
            results = []
            for ticker in tickers:
                try:
                    # ดึงข้อมูลย้อนหลัง
                    stock = yf.Ticker(ticker)
                    hist = stock.history(period="3mo")
                    if hist.empty or len(hist) < 20:
                        continue
                        
                    current_price = float(hist['Close'].iloc[-1])
                    prev_price = float(hist['Close'].iloc[-2])
                    pct_change = ((current_price - prev_price) / prev_price) * 100
                    
                    # คำนวณเส้นค่าเฉลี่ย SMA 20 วัน
                    hist['SMA20'] = hist['Close'].rolling(window=20).mean()
                    curr_sma = float(hist['SMA20'].iloc[-1])
                    prev_sma = float(hist['SMA20'].iloc[-2])
                    
                    # แยกประเภทสินทรัพย์เพื่อแสดงผลให้สวยงาม
                    asset_type = "คริปโต 🪙" if "-USD" in ticker else "หุ้นไทย 🇹🇭" if ".BK" in ticker else "หุ้นต่างประเทศ 🌎"
                    
                    # เงื่อนไขสัญญาณเข้าซื้อ (Buy Signal = ราคาทะลุเส้นค่าเฉลี่ย 20 วันขึ้นมาได้)
                    signal = "⚪ รอดูสถานการณ์"
                    if prev_price < prev_sma and current_price > curr_sma:
                        signal = "🟢 แนะนำซื้อ (Breakout)"
                    elif current_price > curr_sma:
                        signal = "🟡 ถือรันเทรนด์ (Uptrend)"
                    else:
                        signal = "🔴 แนวโน้มขาลง"
                    
                    results.append({
                        "สัญลักษณ์": ticker,
                        "ประเภท": asset_type,
                        "ราคาปัจจุบัน": current_price,
                        "เปลี่ยนแปลง (%)": pct_change,
                        "แนวรับ (SMA 20)": curr_sma,
                        "คำแนะนำประจำวัน": signal
                    })
                except Exception:
                    pass
            
            # ==========================================
            # 4. ส่วนแสดงผล Dashboard
            # ==========================================
            df_results = pd.DataFrame(results)
            
            if not df_results.empty:
                st.markdown("---")
                
                # กรองเฉพาะตัวที่ "น่าเข้าซื้อประจำวัน"
                buy_df = df_results[df_results['คำแนะนำประจำวัน'] == "🟢 แนะนำซื้อ (Breakout)"]
                
                # 4.1 ไฮไลต์ตัวที่น่าเข้าซื้อประจำวัน
                st.header("🔥 ตัวที่น่าเข้าซื้อประจำวัน (Daily Top Picks)")
                st.markdown("สินทรัพย์ที่มีสัญญาณเชิงบวก (ราคากำลังพุ่งทะลุเส้นค่าเฉลี่ย 20 วันในวันนี้)")
                
                if not buy_df.empty:
                    # แสดงเป็นแบบการ์ด (Metrics) สำหรับตัวที่น่าซื้อ
                    cols = st.columns(len(buy_df) if len(buy_df) <= 4 else 4)
                    for i, row in buy_df.reset_index().iterrows():
                        col = cols[i % 4]
                        with col:
                            st.metric(
                                label=f"{row['สัญลักษณ์']} ({row['ประเภท'].split()[0]})", 
                                value=f"{row['ราคาปัจจุบัน']:.2f}", 
                                delta=f"{row['เปลี่ยนแปลง (%)']:.2f}%"
                            )
                    
                    st.dataframe(
                        buy_df.style.format({
                            "ราคาปัจจุบัน": "{:.2f}",
                            "เปลี่ยนแปลง (%)": "{:.2f}%",
                            "แนวรับ (SMA 20)": "{:.2f}"
                        }),
                        use_container_width=True, hide_index=True
                    )
                else:
                    st.info("ตลาดวันนี้ยังไม่มีสินทรัพย์ตัวไหนเกิดสัญญาณ 'Breakout' เพื่อเข้าซื้อครับ แนะนำให้รอดูสถานการณ์ไปก่อน")
                
                st.markdown("<br><br>", unsafe_allow_html=True)
                
                # 4.2 ตารางสรุปภาพรวมทั้งหมด
                st.subheader("📊 ภาพรวมสินทรัพย์ทั้งหมดใน Track set")
                
                def color_signal(val):
                    if "🟢" in val: return 'background-color: #e6f9ec; color: #006400; font-weight: bold;'
                    elif "🟡" in val: return 'color: #b8860b;'
                    elif "🔴" in val: return 'color: #8b0000;'
                    return ''

                def color_pct(val):
                    color = '#00C853' if val > 0 else '#D50000' if val < 0 else 'gray'
                    return f'color: {color}; font-weight: bold;'
                
                st.dataframe(
                    df_results.style
                    .map(color_pct, subset=['เปลี่ยนแปลง (%)'])
                    .map(color_signal, subset=['คำแนะนำประจำวัน'])
                    .format({
                        "ราคาปัจจุบัน": "{:.2f}",
                        "เปลี่ยนแปลง (%)": "{:.2f}%",
                        "แนวรับ (SMA 20)": "{:.2f}"
                    }),
                    use_container_width=True, height=600, hide_index=True
                )
                
            else:
                st.error("ไม่สามารถดึงข้อมูลได้ โปรดตรวจสอบการเชื่อมต่ออินเทอร์เน็ตหรือรายชื่อสัญลักษณ์อีกครั้ง")

else:
    # หน้าจอตอนเริ่มต้น
    st.info("👈 กรุณาอัปโหลดไฟล์ **Track set** ของคุณที่แถบด้านซ้ายมือเพื่อเริ่มต้น")
    
    st.markdown("""
    ### 📝 คำแนะนำการเตรียมไฟล์ Track set
    เพื่อติดตามสินทรัพย์จากทั่วโลก ให้คุณนำสัญลักษณ์ของ **Yahoo Finance** มาใส่ในคอลัมน์แรกของไฟล์ Excel หรือ CSV
    
    **ตัวอย่างการพิมพ์สัญลักษณ์ (Ticker):**
    *   **🇹🇭 หุ้นไทย:** ต้องมี `.BK` ต่อท้ายเสมอ เช่น `PTT.BK`, `AOT.BK`, `CPALL.BK`
    *   **🌎 หุ้นอเมริกา:** ใช้ชื่อตรงๆ ได้เลย เช่น `AAPL` (Apple), `TSLA` (Tesla), `NVDA` (NVIDIA)
    *   **🪙 คริปโตเคอร์เรนซี:** ใช้สัญลักษณ์คู่เหรียญดอลลาร์ เช่น `BTC-USD` (Bitcoin), `ETH-USD` (Ethereum), `DOGE-USD` (Dogecoin)
    """)
