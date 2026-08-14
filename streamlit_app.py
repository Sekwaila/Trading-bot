@@
-    regime=result.get("regime",{}); st.markdown("### 📈 REGIME"); st.metric("Regime",regime.get("regime","UNKNOWN")); st.write(f"ADX: **{num(regime.get('adx')):.2f}** | Vol Ratio: **{num(regime[...]")
+    regime=result.get("regime",{}); st.markdown("### 📈 REGIME"); st.metric("Regime",regime.get("regime","UNKNOWN")); st.write(f"ADX: **{num(regime.get('adx')):.2f}** | Vol Ratio: **{num(regime.get('vol_ratio'),0):.2f}**")
@@
-    st.markdown("### 💎 PREMIUM / DISCOUNT"); pd_info=result.get("pd_info",{}); st.metric("Zone",result.get("pd_zone","UNKNOWN")); st.write(f"Equilibrium: **{price(pd_info.get('equilibrium'))}*[...] 
+    st.markdown("### 💎 PREMIUM / DISCOUNT"); pd_info=result.get("pd_info",{}); st.metric("Zone",result.get("pd_zone","UNKNOWN")); st.write(f"Equilibrium: **{price(pd_info.get('equilibrium'))}**")
