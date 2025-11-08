#!/usr/bin/env python3
"""
AgentNote 主程序入口
"""

import os
import sys
from agentnote.agents.note_agent import NoteAgent
from agentnote.utils.config_loader import load_config_from_yaml

def main():
    """主函数"""
    # 加载配置
    load_config_from_yaml("config.yaml")
    
    # 检查API密钥
    api_key = os.getenv('DEEPSEEK_API_KEY') or input("请输入DeepSeek API密钥: ")
    if not api_key:
        print("错误: 需要提供DeepSeek API密钥")
        return
    
    # 创建智能体
    agent = NoteAgent(api_key)
    
    print("=== AgentNote 智能体系统 ===")
    print("输入 'quit' 或 'exit' 退出程序")
    print("输入 'status' 查看当前状态")
    print("输入 'help' 查看帮助")
    print()
    
    while True:
        try:
            user_input = input("\n请输入任务描述: ").strip()
            
            if user_input.lower() in ['quit', 'exit']:
                print("再见!")
                break
            elif user_input.lower() == 'status':
                status = agent.get_status()
                print(f"当前状态: {status}")
                continue
            elif user_input.lower() == 'help':
                print_help()
                continue
            elif not user_input:
                continue
            
            # 执行任务
            success = agent.run_task(user_input)
            
            if success:
                print("✅ 任务执行成功!")
            else:
                print("❌ 任务执行失败!")
                
        except KeyboardInterrupt:
            print("\n\n程序被用户中断")
            break
        except Exception as e:
            print(f"发生错误: {e}")

def print_help():
    """打印帮助信息"""
    help_text = """
可用命令:
- 直接输入任务描述: 执行自动化任务
- status: 查看当前执行状态
- help: 显示此帮助信息
- quit/exit: 退出程序

示例任务:
- "加载和分析本地的test.dot，并用networkx可视化"
    """
    print(help_text)

if __name__ == "__main__":
    main()