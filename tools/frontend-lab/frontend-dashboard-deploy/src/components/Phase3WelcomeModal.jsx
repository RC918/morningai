import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Users, Shield, UserCog } from 'lucide-react';

export function Phase3WelcomeModal({ isOpen, onClose }) {
  const navigate = useNavigate();
  
  const handleGoToSettings = () => {
    onClose();
    navigate('/tenant-settings');
  };
  
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle className="text-2xl">🎉 歡迎使用全新 Morning AI！</DialogTitle>
          <DialogDescription className="text-base font-semibold text-gray-900 pt-2">
            團隊協作功能現已上線
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          <div className="flex items-start gap-3">
            <Users className="w-6 h-6 text-blue-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">團隊管理</p>
              <p className="text-sm text-gray-600">
                在「系統設置」中查看和管理您的團隊成員
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <Shield className="w-6 h-6 text-green-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">增強安全性</p>
              <p className="text-sm text-gray-600">
                企業級資料隔離，確保您的數據安全
              </p>
            </div>
          </div>
          
          <div className="flex items-start gap-3">
            <UserCog className="w-6 h-6 text-purple-500 mt-1" />
            <div className="space-y-1">
              <p className="font-semibold text-gray-900">角色權限</p>
              <p className="text-sm text-gray-600">
                靈活的成員角色管理：擁有者、管理員、成員、查看者
              </p>
            </div>
          </div>
          
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mt-4">
            <p className="text-sm text-blue-900">
              ℹ️ 您的歷史數據已安全遷移，無需任何操作即可繼續使用
            </p>
          </div>
        </div>
        
        <DialogFooter className="gap-2">
          <Button variant="outline" onClick={onClose}>
            稍後再說
          </Button>
          <Button onClick={handleGoToSettings}>
            查看團隊設置
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
