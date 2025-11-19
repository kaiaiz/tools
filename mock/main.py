#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mock服务 - 用于模拟API接口
基于配置文件动态加载接口定义，支持灵活的Mock数据配置
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import copy
import re


class ConfigLoader:
    """配置加载器 - 负责加载和解析配置文件"""
    
    def __init__(self, config_path: str = 'config.json'):
        """
        初始化配置加载器
        
        Args:
            config_path: 配置文件路径，默认为config.json
        """
        self.config_path = config_path
        self.config = None
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """
        加载配置文件
        
        Returns:
            配置字典
            
        Raises:
            FileNotFoundError: 配置文件不存在
            json.JSONDecodeError: 配置文件格式错误
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"配置文件不存在: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        return self.config
    
    def get_server_config(self) -> Dict[str, Any]:
        """获取服务器配置"""
        return self.config.get('server', {})
    
    def get_endpoints(self) -> List[Dict[str, Any]]:
        """获取所有接口定义"""
        return self.config.get('endpoints', [])
    
    def get_global_settings(self) -> Dict[str, Any]:
        """获取全局设置"""
        return self.config.get('global_settings', {})


class ResponseBuilder:
    """响应构建器 - 负责根据模板构建响应数据"""
    
    def __init__(self, global_settings: Dict[str, Any]):
        """
        初始化响应构建器
        
        Args:
            global_settings: 全局设置
        """
        self.global_settings = global_settings
    
    def build_response(self, template: Dict[str, Any], endpoint_config: Dict[str, Any], 
                      server_port: int) -> Dict[str, Any]:
        """
        根据模板构建响应数据
        
        Args:
            template: 响应模板
            endpoint_config: 接口配置
            server_port: 服务器端口
    
    Returns:
            构建好的响应数据
        """
        # 深拷贝模板，避免修改原始配置
        response_data = copy.deepcopy(template)
        
        # 获取请求信息
        request_info = self._get_request_info()
        
        # 替换模板变量
        response_data = self._replace_template_variables(
            response_data, 
            request_info, 
            endpoint_config,
            server_port
        )
        
        return response_data
    
    def _get_request_info(self) -> Dict[str, Any]:
        """获取当前请求信息"""
        # 获取请求头信息（保留原始大小写）
        headers = self._get_original_headers()
        
        # 获取请求体数据（如果有）
        request_data = None
        if request.is_json:
            request_data = request.get_json()
        elif request.data:
            try:
                request_data = json.loads(request.data.decode('utf-8'))
            except:
                request_data = request.data.decode('utf-8', errors='ignore')
        
        # 获取URL查询参数
        request_args = dict(request.args)
        
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'request_method': request.method,
            'request_headers': headers,
            'request_data': request_data,
            'request_args': request_args,
            'request_url': request.url,
            'request_path': request.path,
            'request_remote_addr': request.remote_addr
        }
        
    def _get_original_headers(self) -> Dict[str, str]:
        """
        获取原始请求头（尽可能保留大小写）
        
        注意：由于WSGI规范的限制，HTTP请求头在environ中会被转换为大写，
        并且连字符会被替换为下划线。我们无法完全还原原始大小写，但会尝试
        智能还原为常见的HTTP请求头格式。
        
        在WSGI环境中：
        - AuthorizationKey -> HTTP_AUTHORIZATIONKEY
        - Authorization-Key -> HTTP_AUTHORIZATION_KEY
        - Content-Type -> HTTP_CONTENT_TYPE
        
        Returns:
            尽可能保留原始格式的请求头字典
        """
        headers_dict = {}
        
        # 从environ中读取所有HTTP_开头的键
        for key, value in request.environ.items():
            if key.startswith('HTTP_'):
                # 移除HTTP_前缀
                header_key = key[5:]
                
                # 检查是否包含下划线（说明原始请求头可能有连字符）
                if '_' in header_key:
                    # 将下划线替换为连字符
                    header_key = header_key.replace('_', '-')
                    # 还原为Title Case格式（每个单词首字母大写）
                    # 例如：AUTHORIZATION-KEY -> Authorization-Key
                    header_key = self._restore_header_case(header_key)
                else:
                    # 没有下划线，说明原始请求头可能是驼峰命名或单个单词
                    # 例如：AUTHORIZATIONKEY -> AuthorizationKey
                    # 尝试检测可能的单词边界（通过检测连续的大写字母）
                    # 并还原为驼峰命名格式
                    header_key = self._restore_camel_case(header_key)
                
                headers_dict[header_key] = value
        
        # 如果headers_dict为空，回退到request.headers（小写版本）
        if not headers_dict:
            headers_dict = dict(request.headers)
        
        return headers_dict
    
    def _restore_header_case(self, header_name: str) -> str:
        """
        还原请求头的大小写格式（Title Case）
        
        将大写的请求头名称转换为Title Case格式：
        - 每个单词首字母大写，其余小写
        - 例如：AUTHORIZATION-KEY -> Authorization-Key
        - 例如：CONTENT-TYPE -> Content-Type
        
        Args:
            header_name: 大写的请求头名称（用连字符分隔）
            
        Returns:
            还原后的请求头名称（Title Case格式）
        """
        # 将连字符分隔的单词转换为Title Case
        parts = header_name.split('-')
        restored_parts = []
        for part in parts:
            if part:
                # 首字母大写，其余小写
                restored_parts.append(part.capitalize())
            else:
                restored_parts.append('-')
        return '-'.join(restored_parts)
    
    def _restore_camel_case(self, header_name: str) -> str:
        """
        尝试还原驼峰命名的请求头
        
        对于没有连字符的请求头，尝试检测可能的单词边界并还原为驼峰命名。
        例如：AUTHORIZATIONKEY -> AuthorizationKey
        
        注意：由于WSGI已经将所有字符转为大写，我们无法完全还原原始大小写。
        此方法会尝试通过检测常见的单词模式来还原。
        
        Args:
            header_name: 大写的请求头名称（单个单词，无连字符）
            
        Returns:
            尝试还原后的请求头名称（尽可能接近驼峰命名）
        """
        # 如果全部是大写，尝试检测可能的单词边界
        # 方法：检测连续的大写字母，假设它们是单词的首字母
        # 例如：AUTHORIZATIONKEY -> AuthorizationKey
        
        # 简单方法：检测常见的前缀模式
        # 但更实用的方法是：直接使用Title Case（首字母大写，其余小写）
        # 这样至少能保证首字母大写
        
        # 对于像 AuthorizationKey 这样的词，WSGI会存储为 AUTHORIZATIONKEY
        # 我们无法完全还原，但可以尝试检测常见的单词组合
        
        # 检测常见的HTTP请求头前缀
        common_prefixes = ['AUTHORIZATION', 'CONTENT', 'ACCEPT', 'USER', 'X-']
        
        # 如果匹配常见前缀，尝试分离
        for prefix in common_prefixes:
            if header_name.startswith(prefix):
                # 分离前缀和剩余部分
                remaining = header_name[len(prefix):]
                if remaining:
                    # 前缀首字母大写，其余小写；剩余部分首字母大写，其余小写
                    return prefix.capitalize() + remaining.capitalize()
                else:
                    return prefix.capitalize()
        
        # 如果没有匹配的前缀，使用简单的Title Case
        # 但尝试检测可能的单词边界（通过检测连续的大写字母）
        # 简单实现：首字母大写，其余小写
        return header_name.capitalize()
    
    def _replace_template_variables(self, data: Any, request_info: Dict[str, Any], 
                                   endpoint_config: Dict[str, Any], 
                                   server_port: int) -> Any:
        """
        递归替换模板变量
        
        Args:
            data: 要处理的数据（可能是字典、列表或字符串）
            request_info: 请求信息
            endpoint_config: 接口配置
            server_port: 服务器端口
            
        Returns:
            替换后的数据
        """
        if isinstance(data, dict):
            return {k: self._replace_template_variables(v, request_info, endpoint_config, server_port) 
                   for k, v in data.items()}
        elif isinstance(data, list):
            return [self._replace_template_variables(item, request_info, endpoint_config, server_port) 
                   for item in data]
        elif isinstance(data, str):
            # 替换模板变量
            if data == '{{timestamp}}':
                return request_info['timestamp']
            elif data == '{{request_method}}':
                return request_info['request_method']
            elif data == '{{request_headers}}':
                return request_info['request_headers']
            elif data == '{{request_data}}':
                return request_info['request_data']
            elif data == '{{request_args}}':
                return request_info['request_args']
            elif data == '{{request_url}}':
                return request_info['request_url']
            elif data == '{{request_path}}':
                return request_info['request_path']
            elif data == '{{request_remote_addr}}':
                return request_info['request_remote_addr']
            elif data == '{{server_port}}':
                return server_port
            elif data == '{{endpoints_info}}':
                # 构建接口信息字典
                endpoints_info = {}
                for ep in config_loader.get_endpoints():
                    endpoints_info[ep['path']] = ep.get('description', '')
                return endpoints_info
            else:
                return data
        else:
            return data


class RequestValidator:
    """请求验证器 - 负责验证请求是否符合配置要求"""
    
    def __init__(self, validation_config: Dict[str, Any]):
        """
        初始化请求验证器
        
        Args:
            validation_config: 验证配置
        """
        self.validation_config = validation_config
    
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        验证请求
        
        Returns:
            (是否通过验证, 错误信息)
        """
        # 验证必需的请求头
        required_headers = self.validation_config.get('required_headers', [])
        for header in required_headers:
            if header not in request.headers:
                return False, f"缺少必需的请求头: {header}"
        
        # 验证必需的查询参数
        required_params = self.validation_config.get('required_params', [])
        for param in required_params:
            if param not in request.args:
                return False, f"缺少必需的查询参数: {param}"
        
        # 验证必需的请求体字段
        required_body_fields = self.validation_config.get('required_body_fields', [])
        if required_body_fields:
            request_data = None
            if request.is_json:
                request_data = request.get_json()
            elif request.data:
                try:
                    request_data = json.loads(request.data.decode('utf-8'))
                except:
                    pass
            
            if not request_data:
                return False, "请求体为空，但配置要求必需字段"
            
            for field in required_body_fields:
                if field not in request_data:
                    return False, f"缺少必需的请求体字段: {field}"
        
        return True, None


# 初始化配置加载器
config_loader = ConfigLoader()

# 创建Flask应用实例
app = Flask(__name__)

# 根据配置启用CORS
global_settings = config_loader.get_global_settings()
if global_settings.get('enable_cors', True):
    CORS(app)

# 初始化响应构建器
response_builder = ResponseBuilder(global_settings)

# 获取服务器配置
server_config = config_loader.get_server_config()
SERVER_PORT = server_config.get('port', 8011)


def create_endpoint_handler(endpoint_config: Dict[str, Any]):
    """
    创建接口处理函数
    
    Args:
        endpoint_config: 接口配置
        
    Returns:
        处理函数
    """
    def handler():
        """
        接口处理函数
        根据配置处理请求并返回响应
        """
        try:
            # 请求验证
            validation_config = endpoint_config.get('request_validation', {})
            if validation_config:
                validator = RequestValidator(validation_config)
                is_valid, error_msg = validator.validate()
                if not is_valid:
                    error_status = global_settings.get('default_error_status', 400)
                    return jsonify({
                        'status': error_status,
                        'message': error_msg,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }), error_status
            
            # 记录请求日志
            if endpoint_config.get('log_request', False):
                _log_request(endpoint_config)
            
            # 构建响应
            response_template = endpoint_config['response']['template']
            response_data = response_builder.build_response(
                response_template, 
                endpoint_config, 
                SERVER_PORT
            )
            
            # 获取响应状态码
            status_code = endpoint_config['response'].get('status_code', 200)
            
            return jsonify(response_data), status_code
            
        except Exception as e:
            # 错误处理
            error_status = global_settings.get('default_error_status', 500)
            error_message = global_settings.get('default_error_message', '服务器内部错误')
            error_response = {
                'status': error_status,
                'message': f'{error_message}: {str(e)}',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            print(f"错误: {str(e)}")
            return jsonify(error_response), error_status
    
    # 设置函数名称，方便调试
    handler.__name__ = f"handle_{endpoint_config['path'].replace('/', '_').replace(' ', '_')}"
    return handler


def _log_request(endpoint_config: Dict[str, Any]):
    """
    记录请求日志
    
    Args:
        endpoint_config: 接口配置
    """
    # 使用响应构建器的方法获取原始请求头（保留大小写）
    headers = response_builder._get_original_headers()
    request_data = None
    if request.is_json:
        request_data = request.get_json()
    elif request.data:
        try:
            request_data = json.loads(request.data.decode('utf-8'))
        except:
            request_data = request.data.decode('utf-8', errors='ignore')
    request_args = dict(request.args)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.path}")
    print(f"请求头: {json.dumps(headers, ensure_ascii=False, indent=2)}")
    if request_data:
        print(f"请求体: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
    if request_args:
        print(f"查询参数: {json.dumps(request_args, ensure_ascii=False, indent=2)}")
    print("-" * 80)
        

# 动态注册所有接口
def register_endpoints():
    """根据配置文件动态注册所有接口"""
    endpoints = config_loader.get_endpoints()
    for endpoint_config in endpoints:
        path = endpoint_config['path']
        methods = endpoint_config.get('methods', ['GET'])
        handler = create_endpoint_handler(endpoint_config)
        app.route(path, methods=methods)(handler)
        print(f"已注册接口: {path} [{', '.join(methods)}]")


# 注册所有接口
register_endpoints()


if __name__ == '__main__':
    """
    启动Flask开发服务器
    根据配置文件中的设置启动服务
    """
    host = server_config.get('host', '0.0.0.0')
    port = server_config.get('port', 8011)
    debug = server_config.get('debug', True)
    
    print("=" * 80)
    print("Mock服务启动中...")
    print(f"服务地址: http://localhost:{port}")
    print(f"配置文件: {config_loader.config_path}")
    print(f"已注册接口数量: {len(config_loader.get_endpoints())}")
    print("-" * 80)
    for endpoint in config_loader.get_endpoints():
        methods_str = ', '.join(endpoint.get('methods', ['GET']))
        print(f"  {endpoint['path']} [{methods_str}] - {endpoint.get('description', '')}")
    print("=" * 80)
    
    # 启动服务器
    app.run(host=host, port=port, debug=debug)
