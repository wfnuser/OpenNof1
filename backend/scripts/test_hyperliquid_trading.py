"""Simple smoke test for Hyperliquid trader"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

script_dir = Path(__file__).parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

env_file = backend_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

from trading.factory import get_exchange_trader  # noqa: E402


async def test_hyperliquid_trader():
    print("🧪 Hyperliquid Trader Smoke Test")
    try:
        trader = get_exchange_trader("hyperliquid")
    except ValueError as exc:
        print(f"❌ 无法创建 Hyperliquid 交易器: {exc}")
        print("请确认 agent.yaml 中已启用 exchanges.hyperliquid 且钱包环境变量有效。")
        return

    print(f"✅ 交易所: {trader.get_exchange_name()}")

    print("\n📊 获取账户余额...")
    balance = await trader.get_balance()
    print(
        f"总余额 {balance.total_balance} {balance.currency} | 可用 {balance.available_balance} | 未实现盈亏 {balance.unrealized_pnl}"
    )

    print("\n📈 获取持仓...")
    positions = await trader.get_positions()
    if not positions:
        print("没有持仓")
    else:
        for pos in positions:
            print(
                f"  {pos.symbol} {pos.side} size={pos.size} entry={pos.entry_price} pnl={pos.unrealized_pnl} leverage={pos.leverage}"
            )

    print("\n💰 获取市场价格...")
    eth_price = await trader.get_market_price("ETH/USDC:USDC")
    print(f"ETH/USDC:USDC 价格: {eth_price}")

    print("\n🔢 数量格式化...")
    formatted_qty = trader.format_quantity("ETH/USDC:USDC", 0.123456)
    print(f"格式化结果: {formatted_qty}")

    print("\n🧹 取消测试挂单...")
    success = await trader.cancel_all_orders("ETH/USDC:USDC")
    print("取消状态: ", "成功" if success else "失败")

    # Optional live order test (use tiny size)
    try:
        print("\n🚀 测试下单流程 (ETH/USDC:USDC 小额开平仓)...")
        eth_price = await trader.get_market_price("ETH/USDC:USDC")
        if eth_price <= 0:
            raise ValueError("无法获取 ETH/USDT 价格")

        test_value = 12  # USD (must exceed $10 minimum)
        quantity = max(0.0001, test_value / eth_price)
        print(f"当前 ETH 价格: {eth_price}, 测试下单数量: {quantity}")

        order = await trader.open_long("ETH/USDC:USDC", quantity, leverage=1)
        print("开多成功, 订单ID:", order.get("id"))

        # 重新获取持仓，按实际合约数量平仓
        positions = await trader.get_positions()
        long_position = next((p for p in positions if p.symbol == "ETH/USDC:USDC" and p.side == "LONG"), None)
        if not long_position:
            raise ValueError("开多后未发现持仓，无法平仓")

        close_order = await trader.close_long("ETH/USDC:USDC", long_position.size)
        print("平多成功, 订单ID:", close_order.get("id"))
    except Exception as exc:
        print(f"⚠️ 下单测试失败: {exc}")

    print("\n✅ Hyperliquid 接口基本检查完成")


if __name__ == "__main__":
    asyncio.run(test_hyperliquid_trader())
