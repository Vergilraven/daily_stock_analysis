#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
钉钉机器人通知脚本
用于发送股票分析报告到钉钉群
"""

import os
import json
import requests
import sys
from datetime import datetime
import mimetypes


def send_dingtalk_file(webhook_url, file_path):
    """
    发送文件到钉钉
    
    Args:
        webhook_url (str): 钉钉机器人Webhook地址
        file_path (str): 文件路径
    
    Returns:
        bool: 发送是否成功
    """
    try:
        # 获取文件类型
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = 'application/octet-stream'
        
        # 读取文件内容
        with open(file_path, 'rb') as f:
            files = {
                'media': (os.path.basename(file_path), f, mime_type)
            }
            
            # 获取上传凭证
            upload_url = webhook_url.replace('/robot/send?', '/media/upload?').replace('https://oapi.dingtalk.com', 'https://oapi.dingtalk.com')
            params = {'type': 'file'}
            response = requests.post(upload_url, params=params, files=files)
            
            if response.status_code == 200 and response.json().get('errcode') == 0:
                media_id = response.json().get('media_id')
                
                # 发送文件消息
                headers = {'Content-Type': 'application/json'}
                payload = {
                    'msgtype': 'file',
                    'file': {
                        'media_id': media_id
                    }
                }
                
                send_response = requests.post(webhook_url, headers=headers, json=payload)
                result = send_response.json()
                
                if result.get('errcode') == 0:
                    print(f"文件 {file_path} 发送成功")
                    return True
                else:
                    print(f"文件发送失败: {result}")
                    return False
            else:
                print(f"媒体上传失败: {response.text}")
                return False
                
    except Exception as e:
        print(f"发送文件时出错: {e}")
        return False


def send_dingtalk_message(webhook_url, content):
    """
    发送文本消息到钉钉
    
    Args:
        webhook_url (str): 钉钉机器人Webhook地址
        content (str): 消息内容
    
    Returns:
        bool: 发送是否成功
    """
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'msgtype': 'text',
            'text': {
                'content': content
            }
        }
        
        response = requests.post(webhook_url, headers=headers, json=payload)
        result = response.json()
        
        if result.get('errcode') == 0:
            print("消息发送成功")
            return True
        else:
            print(f"消息发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"发送消息时出错: {e}")
        return False


def send_dingtalk_markdown(webhook_url, title, text):
    """
    发送Markdown消息到钉钉
    
    Args:
        webhook_url (str): 钉钉机器人Webhook地址
        title (str): 标题
        text (str): Markdown格式的消息内容
    
    Returns:
        bool: 发送是否成功
    """
    try:
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            'msgtype': 'markdown',
            'markdown': {
                'title': title,
                'text': text
            }
        }
        
        response = requests.post(webhook_url, headers=headers, json=payload)
        result = response.json()
        
        if result.get('errcode') == 0:
            print("Markdown消息发送成功")
            return True
        else:
            print(f"Markdown消息发送失败: {result}")
            return False
            
    except Exception as e:
        print(f"发送Markdown消息时出错: {e}")
        return False


def get_latest_report_files(reports_dir="reports"):
    """获取最新的报告文件"""
    if not os.path.exists(reports_dir):
        return []
    
    report_files = []
    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith(('.txt', '.md', '.pdf', '.html')):
                file_path = os.path.join(root, file)
                report_files.append((file_path, os.path.getmtime(file_path)))
    
    # 按修改时间排序，返回最新文件
    report_files.sort(key=lambda x: x[1], reverse=True)
    return [f[0] for f in report_files[:10]]  # 返回最新的10个文件


def main():
    """主函数"""
    # 从环境变量获取钉钉Webhook URL
    dingtalk_webhook = os.getenv('DINGTALK_WEBHOOK_URL')
    if not dingtalk_webhook:
        print("错误: 未设置 DINGTALK_WEBHOOK_URL 环境变量")
        sys.exit(1)
    
    print("开始发送钉钉通知...")
    
    # 发送状态消息
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    status_msg = f"📊 股票分析报告已生成\n时间: {current_time}\n主机: {os.uname().nodename if hasattr(os, 'uname') else 'Unknown'}"
    
    success = send_dingtalk_message(dingtalk_webhook, status_msg)
    
    if not success:
        print("初始状态消息发送失败，停止发送其他消息")
        sys.exit(1)
    
    # 获取并发送最新报告文件
    latest_reports = get_latest_report_files()
    
    if not latest_reports:
        print("未找到报告文件")
        # 发送没有报告的通知
        no_report_msg = "⚠️ 本次分析未生成任何报告文件"
        send_dingtalk_message(dingtalk_webhook, no_report_msg)
    else:
        print(f"发现 {len(latest_reports)} 个报告文件")
        
        # 发送摘要信息
        summary_text = f"📈 本次分析共生成 {len(latest_reports)} 份报告\n\n"
        summary_text += "📁 报告文件列表:\n"
        for i, file_path in enumerate(latest_reports, 1):
            file_size = os.path.getsize(file_path)
            size_str = f"{file_size / 1024:.1f}KB" if file_size > 1024 else f"{file_size}B"
            summary_text += f"{i}. {os.path.basename(file_path)} ({size_str})\n"
        
        # 发送摘要到钉钉
        send_dingtalk_markdown(
            dingtalk_webhook,
            "股票分析报告摘要",
            summary_text
        )
        
        # 发送报告文件（限制发送数量，避免太多文件）
        max_files_to_send = 5
        sent_count = 0
        
        for report_file in latest_reports:
            if sent_count >= max_files_to_send:
                break
                
            print(f"正在发送文件: {report_file}")
            if send_dingtalk_file(dingtalk_webhook, report_file):
                sent_count += 1
            else:
                print(f"文件发送失败: {report_file}")
    
    print("钉钉通知发送完成")


if __name__ == "__main__":
    main()
