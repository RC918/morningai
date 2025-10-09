#!/usr/bin/env python3
"""
Docker-based sandbox implementation
"""
import asyncio
import logging
import docker
from typing import Optional

class DockerSandbox:
    """Docker-based agent sandbox"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = docker.from_env()
        self.container = None
    
    async def create(self) -> str:
        """Create and start Docker container"""
        try:
            image_name = f"morningai-sandbox-{self.config.agent_type}:latest"
            
            container_config = {
                'image': image_name,
                'name': f"sandbox-{self.config.agent_id}",
                'detach': True,
                'remove': False,
                
                'mem_limit': f"{self.config.memory_limit_mb}m",
                'cpu_period': 100000,
                'cpu_quota': int(100000 * self.config.cpu_limit),
                'pids_limit': 100,
                
                'security_opt': [
                    'no-new-privileges:true',
                    'seccomp=default'
                ],
                'cap_drop': ['ALL'],
                'cap_add': ['NET_BIND_SERVICE'],
                'read_only': True,
                
                'tmpfs': {'/tmp': 'size=1G,mode=1777'},
                'volumes': {
                    f'sandbox-{self.config.agent_id}-workspace': {
                        'bind': '/workspace',
                        'mode': 'rw'
                    }
                },
                
                'environment': {
                    'AGENT_ID': self.config.agent_id,
                    'AGENT_TYPE': self.config.agent_type,
                    'MCP_SERVER_URL': 'http://host.docker.internal:8080'
                },
                
                'network_mode': 'bridge' if self.config.network_enabled else 'none'
            }
            
            self.container = self.client.containers.run(**container_config)
            
            self.logger.info(f"Docker container {self.container.id} created for {self.config.agent_id}")
            return self.container.id
            
        except Exception as e:
            self.logger.error(f"Failed to create Docker container: {e}")
            raise
    
    async def destroy(self, container_id: str) -> bool:
        """Stop and remove Docker container"""
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
            
            self.logger.info(f"Docker container {container_id} destroyed")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to destroy Docker container: {e}")
            return False
    
    def get_mcp_endpoint(self) -> str:
        """Get MCP server endpoint for this sandbox"""
        if self.container:
            network_settings = self.container.attrs['NetworkSettings']
            ip_address = network_settings['IPAddress']
            return f"http://{ip_address}:8080"
        return None
