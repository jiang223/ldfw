"""
ldfw - 手游模拟器自动化脚本框架
入口脚本
"""
import argparse
import sys

from core.config_manager import ConfigManager
from core.engine import Engine
from core.logger import get_logger

logger = get_logger("main")

def parse_args():
    parser = argparse.ArgumentParser(description="ldfw 手游模拟器自动化脚本框架")
    parser.add_argument(
        "--config",
        type=str,
        default="config/example_config.json",
        help="配置文件路径（默认：config/example_config.json）",
    )
    parser.add_argument(
        "--module",
        type=str,
        default=None,
        help="指定执行的模块名称，不填则执行全部启用模块",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出配置文件中所有模块",
    )
    return parser.parse_args()

def main():
    args = parse_args()

    logger.info("ldfw 启动")
    logger.info(f"加载配置文件: {args.config}")

    try:
        config_manager = ConfigManager(args.config)
        config_manager.load()
    except FileNotFoundError:
        logger.error(f"配置文件不存在: {args.config}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"配置文件加载失败: {e}")
        sys.exit(1)

    if args.list:
        modules = config_manager.get_all_modules()
        logger.info(f"共 {len(modules)} 个模块：")
        for idx, mod in enumerate(modules, 1):
            status = "✅ 启用" if mod.enabled else "❌ 禁用"
            logger.info(f"  {idx}. [{status}] {mod.name} - 包含 {len(mod.flows)} 个流程")
        return

    engine = Engine(config_manager)

    if args.module:
        logger.info(f"执行指定模块: {args.module}")
        engine.run_module_by_name(args.module)
    else:
        logger.info("执行全部启用模块")
        engine.run_all()

    logger.info("ldfw 执行完毕")

if __name__ == "__main__":
    main()