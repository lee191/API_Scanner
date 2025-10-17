import { useState, useEffect, useCallback } from 'react';
import { toast } from '@/lib/toast';
import { parseErrorMessage } from '@/lib/utils';
import apiService from '@/services/api';
import type { Project, ProjectCreateRequest, ProjectUpdateRequest } from '@/types';

export const useProjects = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedProject, setSelectedProject] = useState<string | null>(null);

  // 프로젝트 목록 로드
  const loadProjects = useCallback(async () => {
    try {
      setLoading(true);
      const data = await apiService.getProjects();
      setProjects(data);
    } catch (err) {
      const message = parseErrorMessage(err);
      if (process.env.NODE_ENV === 'development') {
        console.error('Failed to load projects:', err);
      }
      toast.error(`프로젝트 목록 로드 실패: ${message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  // 프로젝트 생성
  const createProject = useCallback(async (data: ProjectCreateRequest): Promise<boolean> => {
    if (!data.name.trim()) {
      toast.warning('프로젝트 이름을 입력해주세요');
      return false;
    }

    try {
      setLoading(true);
      const project = await apiService.createProject(data);
      await loadProjects();
      setSelectedProject(project.id);
      toast.success('프로젝트가 생성되었습니다');
      return true;
    } catch (err) {
      const message = parseErrorMessage(err);
      toast.error(`프로젝트 생성 실패: ${message}`);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadProjects]);

  // 프로젝트 수정
  const updateProject = useCallback(async (
    projectId: string,
    data: ProjectUpdateRequest
  ): Promise<boolean> => {
    if (!data.name?.trim()) {
      toast.warning('프로젝트 이름을 입력해주세요');
      return false;
    }

    try {
      setLoading(true);
      await apiService.updateProject(projectId, data);
      await loadProjects();
      toast.success('프로젝트가 수정되었습니다');
      return true;
    } catch (err) {
      const message = parseErrorMessage(err);
      toast.error(`프로젝트 수정 실패: ${message}`);
      return false;
    } finally {
      setLoading(false);
    }
  }, [loadProjects]);

  // 프로젝트 삭제
  const deleteProject = useCallback(async (projectId: string): Promise<boolean> => {
    if (!confirm('이 프로젝트를 삭제하시겠습니까? 모든 스캔 기록이 함께 삭제됩니다.')) {
      return false;
    }

    try {
      setLoading(true);
      await apiService.deleteProject(projectId);

      // 삭제된 프로젝트가 선택된 프로젝트인 경우 선택 해제
      if (selectedProject === projectId) {
        setSelectedProject(null);
      }

      await loadProjects();
      toast.success('프로젝트가 삭제되었습니다');
      return true;
    } catch (err) {
      const message = parseErrorMessage(err);
      toast.error(`프로젝트 삭제 실패: ${message}`);
      return false;
    } finally {
      setLoading(false);
    }
  }, [selectedProject, loadProjects]);

  // 초기 로드
  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  return {
    projects,
    loading,
    selectedProject,
    setSelectedProject,
    loadProjects,
    createProject,
    updateProject,
    deleteProject
  };
};
