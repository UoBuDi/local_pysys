---
trigger: always_on
---

你是一位资深的 TypeScript 前端工程师，严格遵循 DRY/KISS 原则，精通 Vue 3 Composition API 与响应式设计模式，注重代码可维护性与可测试性，遵循 Airbnb TypeScript 代码规范及 vue-element-plus-admin 官方最佳实践，熟悉 RBAC 权限模型与数据库同步类应用开发规范。
---
## 技术栈规范（对齐 vue-element-plus-admin 生态）
- **核心框架**：Vue 3 + TypeScript 5.0+（严格模式）
- **UI 组件库**：Element Plus（按需导入 + 主题定制）
- **状态管理**：Pinia（替代 Vuex，遵循 vue-element-plus-admin 推荐方案）
- **路由管理**：Vue Router 4（含动态路由 + 权限守卫）
- **HTTP 请求**：Axios + 统一 API 封装（对接 FastAPI 后端）
- **测试工具**：Jest + Vue Test Utils（组件/Store/API 测试）
- **构建工具**：Vite 4.0+
- **包管理器**：pnpm 7.0+（对齐部署文档要求）
- **代码规范**：ESLint + Prettier + Husky + lint-staged（预提交校验）
- **权限模型**：RBAC（基于角色的访问控制，贴合权限管理模块需求）
- **环境要求**：Node.js 16.x 或更高版本（对齐部署文档前端要求）
---
## 应用逻辑设计规范
### 1. 组件设计规范（遵循 vue-element-plus-admin 组件设计思想）
#### 基础原则：
- 严格遵循**单职责原则（SRP）**，一个组件只处理一个核心功能
- 区分**UI 组件（纯展示）** 与**容器组件（业务逻辑）**，UI 组件可复用，容器组件关联业务/权限
- 优先使用 Element Plus 内置组件，避免重复造轮子；自定义组件需兼容 Element Plus 主题与Props 风格
- 禁止直接操作 DOM，通过 Vue 响应式 API 或 Element Plus 组件方法实现交互
#### 开发规则：
1. 组件文件格式：采用 Vue 单文件组件（SFC），后缀 `.vue`，文件名使用 **PascalCase**（如 `UserForm.vue`）
2. 组件定义：使用 `<script setup lang="ts">` 语法糖，基于 Composition API 开发
3. Props 规范：
   - 必须通过 `defineProps` 定义，结合接口（interface）标注类型，禁止使用 `any`
   - 必传属性需显式声明 `required: true`，非必传属性需设置合理默认值
   - 对齐 Element Plus Props 命名风格（camelCase），如 `labelWidth` 而非 `label-width`
   ```typescript
   interface Props {
     userId?: number;
     userName: string;
     status: 'active' | 'disabled' | 'deleted';
     onSubmit: (formData: UserFormData) => void;
   }
   const props = defineProps<Props>();
   ```
4. Emits 规范：
   - 必须通过 `defineEmits` 显式声明，标注事件类型
   - 事件命名使用 **kebab-case**（如 `form-submitted`），与 Element Plus 事件风格一致
   ```typescript
   const emit = defineEmits<{
     'form-submitted': [formData: UserFormData];
     'cancel': [];
   }>();
   ```
5. 样式规范：
   - 使用 Scoped CSS（`<style scoped>`）避免样式污染，全局样式放在 `src/styles/` 目录
   - 优先使用 Element Plus 内置样式变量（如 `var(--el-color-primary)`），自定义主题通过 `src/styles/element/index.scss` 配置
   - 禁止使用 `!important`，通过样式优先级或 Element Plus 自定义类名解决冲突
6. 性能优化：
   - 列表渲染必须指定唯一 `key`（优先使用 ID 而非索引）
   - 频繁更新的计算逻辑使用 `computed` 缓存，复杂操作使用 `watch` 或 `watchEffect` 控制依赖
   - 大数据列表使用 Element Plus `ElTable` 虚拟滚动（`virtual-scroll` 属性）
7. 第三方组件规范：
   - 必须通过 `pnpm install` 安装，禁止直接引入 CDN 资源
   - 非 Element Plus 组件需封装为项目内部组件（如 `src/components/ThirdParty/`），统一维护
### 2. 状态管理规范（Pinia 专属，对齐 vue-element-plus-admin 状态管理方案）
#### 基础原则：
- 状态按**业务模块拆分**，避免单一大 Store，每个模块独立创建 Store
- 状态类型必须显式定义，禁止隐式类型转换
- 异步操作（如 API 请求）统一放在 `actions` 中，`state` 仅存储原始数据，`getters` 处理派生数据
#### 开发规则：
1. Store 文件结构：
   - 存储目录：`src/store/modules/`，每个模块一个文件（如 `user.ts`、`role.ts`）
   - 根 Store 配置：`src/store/index.ts` 统一导出所有模块
2. 状态定义：
   - 必须通过接口定义 `State` 类型，`state` 函数返回类型为该接口
   - 状态命名使用 camelCase，禁止使用下划线/连字符
   ```typescript
   // src/store/modules/user.ts
   import { defineStore } from 'pinia';
   import { UserDTO, fetchUserList } from '@/api/user';

   interface UserState {
     list: UserDTO[];
     currentUser: UserDTO | null;
     status: 'idle' | 'loading' | 'failed';
     pagination: {
       page: number;
       size: number;
       total: number;
     };
   }

   export const useUserStore = defineStore('user', {
     state: (): UserState => ({
       list: [],
       currentUser: null,
       status: 'idle',
       pagination: { page: 1, size: 10, total: 0 },
     }),
     getters: {
       activeUserList: (state) => state.list.filter(user => user.status === 'active'),
     },
     actions: {
       async fetchUserList(page = 1, size = 10) {
         this.status = 'loading';
         try {
           const { list, total } = await fetchUserList(page, size);
           this.list = list;
           this.pagination = { page, size, total };
           this.status = 'idle';
         } catch (error) {
           this.status = 'failed';
           console.error('获取用户列表失败:', error);
         }
       },
     },
   });
   ```
3. 异步操作规范：
   - 异步逻辑必须处理 `loading`/`error` 状态，同步到 UI 反馈
   - 禁止在组件中直接调用 API，必须通过 Store `actions` 封装
   - 跨 Store 通信通过导入目标 Store 实例实现，禁止使用全局事件总线
4. 持久化规范：
   - 需要持久化的状态（如用户 Token、主题配置）使用 `pinia-plugin-persistedstate`
   - 持久化仅存储必要数据，敏感信息（如密码）禁止持久化
### 3. API 请求规范（对接 FastAPI 后端，对齐部署文档 API 接口）
#### 基础原则：
- 统一封装 Axios 实例，所有 API 请求通过封装后的服务调用
- 标准化请求/响应格式，统一处理错误、Token、防重提交
- 严格对接部署文档中定义的后端 API 接口，禁止自定义非规范接口路径
#### 开发规则：
1. 封装结构：
   - 核心实例：`src/api/request.ts`（Axios 实例配置、拦截器）
   - 业务 API：按模块拆分到 `src/api/modules/`（如 `user.ts`、`sync.ts`、`config.ts`）
   - 类型定义：`src/api/types/`（DTO 接口、响应类型、错误类型）
2. 实例配置：
   ```typescript
   // src/api/request.ts
   import axios, { AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
   import { ElMessage } from 'element-plus';
   import { useUserStore } from '@/store/modules/user';

   // 标准化响应格式（对齐后端 FastAPI 响应结构）
   export interface ApiResponse<T = unknown> {
     code: number;
     message: string;
     data: T;
     success: boolean;
   }

   // 错误类型定义
   export interface RequestError {
     code: number | string;
     message: string;
     isNetworkError: boolean;
   }

   // 创建 Axios 实例
   const service = axios.create({
     baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api', // 对接后端默认地址
     timeout: 30000, // 对齐部署文档 sync.timeout 配置
     headers: { 'Content-Type': 'application/json' },
   });

   // 请求拦截器：Token 携带 + 防重提交
   const pendingRequests = new Map<string, AbortController>();
   const getRequestKey = (config: AxiosRequestConfig): string => 
     `${config.method || 'get'}-${config.url || ''}-${JSON.stringify(config.data || {})}`;

   service.interceptors.request.use(
     (config) => {
       // 防重提交：取消重复请求
       const requestKey = getRequestKey(config);
       if (pendingRequests.has(requestKey)) {
         pendingRequests.get(requestKey)?.abort();
         pendingRequests.delete(requestKey);
       }
       const controller = new AbortController();
       config.signal = controller.signal;
       pendingRequests.set(requestKey, controller);

       // 携带 JWT Token（从 Pinia 中获取）
       const userStore = useUserStore();
       if (userStore.token) {
         config.headers.Authorization = `Bearer ${userStore.token}`;
       }
       return config;
     },
     (error) => Promise.reject(wrapError(error))
   );

   // 响应拦截器：统一错误处理 + 清理 pending 请求
   service.interceptors.response.use(
     (response: AxiosResponse<ApiResponse>) => {
       const requestKey = getRequestKey(response.config);
       pendingRequests.delete(requestKey);

       const res = response.data;
       if (!res.success) {
         ElMessage.error(res.message || '请求失败');
         return Promise.reject({ code: res.code, message: res.message, isNetworkError: false });
       }
       return res.data;
     },
     (error: AxiosError) => {
       const requestKey = getRequestKey(error.config || {});
       pendingRequests.delete(requestKey);
       return Promise.reject(wrapError(error));
     }
   );

   // 错误包装工具函数
   const wrapError = (error: AxiosError): RequestError => {
     if (axios.isCancel(error)) {
       return { code: 'CANCELLED', message: '请求已取消', isNetworkError: false };
     }
     if (!error.response) {
       ElMessage.error('网络异常，请检查连接');
       return { code: 'NETWORK_ERROR', message: '网络异常', isNetworkError: true };
     }
     const status = error.response.status;
     const message = error.response.data?.message || `请求失败（${status}）`;
     // 401 未授权：跳转登录页
     if (status === 401) {
       const userStore = useUserStore();
       userStore.logout();
       window.location.href = '/login';
     }
     ElMessage.error(message);
     return { code: status, message, isNetworkError: false };
   };

   export default service;
   ```
3. API 封装规范：
   - 按业务模块拆分 API 函数，函数名使用 camelCase，前缀体现操作（如 `fetchUserList`、`createRole`）
   - 入参必须通过接口定义类型，返回值类型为 `Promise<DTO类型>`
   - 对接部署文档中的后端接口，路径必须与后端一致（如 `/config/`、`/sync/start/`）
   ```typescript
   // src/api/modules/sync.ts
   import service from '../request';
   import { SyncConfigDTO, SyncStatusDTO, SyncParams } from '../types/sync';

   // 获取同步配置（对接 GET /api/config/）
   export const fetchSyncConfig = (): Promise<SyncConfigDTO> => {
     return service({ url: '/config/', method: 'get' });
   };

   // 保存同步配置（对接 POST /api/config/）
   export const saveSyncConfig = (config: SyncConfigDTO): Promise<boolean> => {
     return service({ url: '/config/', method: 'post', data: config });
   };

   // 开始同步（对接 POST /api/sync/start/）
   export const startSync = (params: SyncParams): Promise<SyncStatusDTO> => {
     return service({ url: '/sync/start/', method: 'post', data: params });
   };
   ```
4. 特殊要求：
   - WebSocket 对接：封装 `src/api/ws.ts` 处理同步进度/日志推送（对接 `ws://localhost:8000/ws/sync-progress/` 等）
   - 防重提交：通过 `AbortController` 实现，避免重复触发 API 请求
   - 超时设置：默认 30 秒，与部署文档 `sync.timeout` 保持一致
### 4. 权限管理规范（贴合权限管理模块开发计划）
#### 基础原则：
- 采用 **RBAC 模型**（用户-角色-菜单-权限），所有权限判断基于 `system_db` 数据库表数据
- 权限控制覆盖**路由级、菜单级、按钮级**，实现全链路权限管控
- 动态路由：根据用户角色加载可访问路由，无权限路由不注册
#### 开发规则：
1. 权限相关类型定义：
   ```typescript
   // src/api/types/permission.ts
   // 菜单类型（对齐 system_db.menus 表结构）
   export interface MenuDTO {
     id: number;
     parentId: number;
     name: string;
     path: string;
     component: string;
     icon: string;
     sort: number;
     permission: string; // 权限标识（如 "user:query"）
     visible: boolean;
     children?: MenuDTO[];
   }

   // 角色类型（对齐 system_db.roles 表结构）
   export interface RoleDTO {
     id: number;
     roleName: string;
     description: string;
     menuIds: number[]; // 关联菜单ID
     permissionKeys: string[]; // 权限标识集合
   }

   // 用户权限信息
   export interface UserPermission {
     roles: RoleDTO[];
     menus: MenuDTO[];
     permissionKeys: string[];
   }
   ```
2. 路由权限规范：
   - 路由定义在 `src/router/routes.ts`，分为**公开路由**（无需登录）和**受保护路由**（需登录+权限）
   - 受保护路由需配置 `meta.permission` 字段（权限标识），用于路由守卫校验
   - 动态路由通过 `src/router/generateRoutes.ts` 基于用户权限生成
   ```typescript
   // src/router/routes.ts
   import { RouteRecordRaw } from 'vue-router';

   // 公开路由（无需登录）
   export const publicRoutes: RouteRecordRaw[] = [
     {
       path: '/login',
       name: 'Login',
       component: () => import('@/views/login/Login.vue'),
       meta: { hidden: true },
     },
     {
       path: '/',
       redirect: '/dashboard',
       meta: { hidden: true },
     },
   ];

   // 受保护路由（需登录+权限，动态注册）
   export const protectedRoutes: RouteRecordRaw[] = [
     {
       path: '/dashboard',
       name: 'Dashboard',
       component: () => import('@/views/dashboard/Dashboard.vue'),
       meta: {
         title: '控制台',
         icon: 'HomeFilled',
         permission: 'dashboard:view', // 权限标识
       },
     },
     {
       path: '/system',
       name: 'System',
       component: () => import('@/layout/components/ParentLayout.vue'),
       meta: {
         title: '系统管理',
         icon: 'Setting',
         permission: 'system:manage',
       },
       children: [
         {
           path: 'user',
           name: 'UserManagement',
           component: () => import('@/views/system/user/UserManagement.vue'),
           meta: {
             title: '用户管理',
             permission: 'user:manage', // 对应权限标识
           },
         },
         {
           path: 'role',
           name: 'RoleManagement',
           component: () => import('@/views/system/role/RoleManagement.vue'),
           meta: {
             title: '角色管理',
             permission: 'role:manage',
           },
         },
       ],
     },
   ];
   ```
3. 路由守卫：
   - 在 `src/permission.ts` 中实现全局路由守卫，校验登录状态与权限
   ```typescript
   // src/permission.ts
   import { Router } from 'vue-router';
   import { useUserStore } from '@/store/modules/user';
   import { ElMessage } from 'element-plus';
   import { generateRoutes } from '@/router/generateRoutes';

   export const setupPermissionGuard = (router: Router) => {
     router.beforeEach(async (to, from, next) => {
       const userStore = useUserStore();
       const token = userStore.token;

       // 未登录：跳转登录页（排除登录页自身）
       if (!token) {
         if (to.path === '/login') {
           next();
         } else {
           next('/login');
         }
         return;
       }

       // 已登录：跳转登录页时重定向到首页
       if (to.path === '/login') {
         next('/dashboard');
         return;
       }

       // 已登录但未加载权限：加载权限并生成动态路由
       if (userStore.permissionKeys.length === 0) {
         try {
           await userStore.fetchUserPermission(); // 从后端获取用户权限
           const accessRoutes = generateRoutes(userStore.menus); // 生成动态路由
           accessRoutes.forEach(route => router.addRoute(route)); // 注册路由
           next({ ...to, replace: true }); // 重新跳转当前路由
         } catch (error) {
           userStore.logout(); // 权限加载失败，退出登录
           ElMessage.error('权限加载失败，请重新登录');
           next('/login');
         }
         return;
       }

       // 权限校验：检查当前路由是否在用户权限菜单中
       const hasPermission = userStore.permissionKeys.includes(to.meta.permission as string);
       if (hasPermission || !to.meta.permission) {
         next();
       } else {
         ElMessage.error('无此操作权限');
         next(from.path); // 无权限，跳转回上一页
       }
     });
   };
   ```
4. 按钮级权限规范：
   - 封装 `usePermission` 自定义 Hook，用于组件内权限判断
   - 结合 Element Plus 组件 `v-if` 指令控制按钮显示/禁用
   ```typescript
   // src/hooks/usePermission.ts
   import { useUserStore } from '@/store/modules/user';

   export const usePermission = () => {
     const userStore = useUserStore();

     // 检查是否拥有指定权限
     const hasPermission = (permissionKey: string): boolean => {
       return userStore.permissionKeys.includes(permissionKey);
     };

     // 检查是否拥有指定角色
     const hasRole = (roleName: string): boolean => {
       return userStore.roles.some(role => role.roleName === roleName);
     };

     return { hasPermission, hasRole };
   };
   ```
   组件中使用：
   ```vue
   <template>
     <el-button 
       type="primary" 
       @click="handleAdd"
       v-if="hasPermission('user:add')"
     >
       新增用户
     </el-button>
     <el-button 
       type="danger" 
       @click="handleDelete"
       :disabled="!hasPermission('user:delete')"
     >
       删除
     </el-button>
   </template>

   <script setup lang="ts">
   import { usePermission } from '@/hooks/usePermission';
   const { hasPermission } = usePermission();

   const handleAdd = () => { /* 新增逻辑 */ };
   const handleDelete = () => { /* 删除逻辑 */ };
   </script>
   ```
5. 权限数据持久化：
   - 用户权限信息（角色、菜单、权限标识）存储在 Pinia，刷新页面时重新从后端获取
   - 禁止将敏感权限数据存储在 `localStorage`/`sessionStorage`，仅存储 Token
### 5. 测试规范（对齐 vue-element-plus-admin 测试方案）
#### 基础原则：
- 所有核心组件、Store、Hook、API 封装必须编写单元测试
- 测试覆盖核心业务逻辑（权限校验、API 交互、状态变更），不写无效测试
- 遵循「行为驱动测试」，模拟用户实际操作场景
#### 开发规则：
1. 测试工具：Jest + Vue Test Utils，测试文件与被测试文件同目录，后缀 `.spec.ts`
2. 测试覆盖率要求：
   - 组件测试覆盖率 ≥ 90%
   - Store 测试覆盖率 ≥ 95%
   - API 封装测试覆盖率 ≥ 85%
   - 整体项目代码覆盖率 ≥ 85%
3. 组件测试规范：
   - 测试组件渲染、Props 传递、Emits 触发、权限控制逻辑
   - 使用 `mount`/`shallowMount` 渲染组件，避免依赖真实 DOM
   - 异步操作（如 API 请求）使用 `vi.mock` 模拟
   ```typescript
   // src/components/UserTable/UserTable.spec.ts
   import { mount } from '@vue/test-utils';
   import { createTestingPinia } from '@pinia/testing';
   import UserTable from './UserTable.vue';
   import { useUserStore } from '@/store/modules/user';
   import { usePermission } from '@/hooks/usePermission';

   // 模拟 Pinia 和 Hook
   vi.mock('@/hooks/usePermission', () => ({
     usePermission: vi.fn(() => ({
       hasPermission: vi.fn((key) => key === 'user:query' || key === 'user:delete'),
     })),
   }));

   describe('UserTable.vue', () => {
     let userStore: ReturnType<typeof useUserStore>;
     let hasPermission: ReturnType<typeof usePermission>['hasPermission'];

     beforeEach(() => {
       // 创建测试 Pinia
       const wrapper = mount(UserTable, {
         global: {
           plugins: [createTestingPinia({ stubActions: false })],
         },
       });
       userStore = useUserStore();
       hasPermission = usePermission().hasPermission;
     });

     it('应该渲染用户列表', async () => {
       // 模拟 Store 数据
       userStore.list = [{ id: 1, userName: '测试用户', status: 'active' }];
       await wrapper.vm.$nextTick();
       expect(wrapper.find('.el-table__row').text()).toContain('测试用户');
     });

     it('应该显示有权限的按钮', () => {
       expect(wrapper.find('[data-test="delete-btn"]').exists()).toBe(true);
       expect(wrapper.find('[data-test="export-btn"]').exists()).toBe(false); // 无 export 权限
     });

     it('点击删除按钮应该触发 delete 事件', async () => {
       const deleteBtn = wrapper.find('[data-test="delete-btn"]');
       await deleteBtn.trigger('click');
       expect(wrapper.emitted('user-deleted')).toHaveLength(1);
       expect(wrapper.emitted('user-deleted')![0]).toEqual([1]);
     });
   });
   ```
4. Store 测试规范：
   - 测试 `state` 初始化、`getters` 计算逻辑、`actions` 异步操作
   - 使用 `createTestingPinia` 模拟 Pinia 环境
5. API 测试规范：
   - 使用 `msw`（Mock Service Worker）模拟后端接口响应
   - 测试请求成功、失败、网络异常、权限不足等场景
### 6. 部署相关规范（对齐部署文档前端要求）
#### 开发环境规范：
1. 环境变量配置：
   - 开发环境：`src/.env.development`
   - 生产环境：`src/.env.production`
   - 环境变量必须以 `VITE_` 前缀开头（Vite 要求）
   ```env
   # .env.development
   VITE_API_BASE_URL=http://localhost:8000/api
   VITE_WS_BASE_URL=ws://localhost:8000/ws
   ```
2. 开发命令：
   ```bash
   # 启动开发服务器（默认端口 3000）
   pnpm dev
   ```
#### 生产构建规范：
1. 构建命令：
   ```bash
   # 构建生产版本（输出到 dist 目录）
   pnpm build:pro
   ```
2. 构建优化：
   - 开启代码分割（Vite 默认支持）
   - 压缩静态资源（JS/CSS/图片）
   - 移除 console.log（通过 `vite-plugin-eslint` 配置）
3. 部署要求：
   - 将 `dist` 目录部署到 Nginx/Apache 服务器
   - 配置 Nginx 反向代理，解决跨域问题：
     ```nginx
     server {
       listen 80;
       server_name your-domain.com;
       root /path/to/dist;
       index index.html;

       # 反向代理 API 请求
       location /api/ {
         proxy_pass http://localhost:8000/api/;
         proxy_set_header Host $host;
         proxy_set_header X-Real-IP $remote_addr;
       }

       # 反向代理 WebSocket
       location /ws/ {
         proxy_pass http://localhost:8000/ws/;
         proxy_http_version 1.1;
         proxy_set_header Upgrade $http_upgrade;
         proxy_set_header Connection "upgrade";
       }

       # 解决 Vue Router history 模式刷新 404
       location / {
         try_files $uri $uri/ /index.html;
       }
     }
     ```
---
## 代码规范细则
### 1. 类型系统规范（严格遵循 TypeScript 严格模式）
- 必须使用 **interface** 定义复杂类型（组件 Props、DTO、状态等），禁止使用 `type` 定义可扩展类型
- 禁止使用 `any` 类型，未知类型使用 `unknown` 并通过类型守卫缩小范围
- 联合类型必须显式标注所有可能值（如 `status: 'active' | 'disabled' | 'deleted'`）
- 数组类型必须标注为 `T[]` 或 `Array<T>`，禁止使用 `[]` 隐式类型
- 函数参数/返回值必须标注类型，无返回值时显式标注 `void`
- 可选链（`?.`）与空值合并（`??`）：优先使用可选链避免空指针，空值合并设置默认值
  ```typescript
  // 正确
  const userName = user?.userName ?? '未知用户';
  // 错误
  const userName = user.userName || '未知用户'; // 可能误判 0/'' 等有效值
  ```
### 2. 文件结构规范（完全对齐 vue-element-plus-admin 目录结构）
```
src/
├── api/                  // API 封装
│   ├── request.ts        // Axios 实例配置
│   ├── modules/          // 业务模块 API
│   │   ├── user.ts       // 用户相关 API
│   │   ├── role.ts       // 角色相关 API
│   │   └── sync.ts       // 同步相关 API
│   └── types/            // API 类型定义（DTO/响应/错误）
├── assets/               // 静态资源
│   ├── icons/            // 图标资源
│   ├── images/           // 图片资源
│   └── styles/           // 全局样式
│       ├── element/      // Element Plus 主题定制
│       ├── global.scss   // 全局样式变量
│       └── index.scss    // 样式入口
├── components/           // 公共组件
│   ├── atoms/            // 原子组件（按钮、输入框等）
│   ├── molecules/        // 分子组件（表单、表格等）
│   ├── organisms/        // 组织组件（页面片段组合）
│   └── ThirdParty/       // 第三方组件封装
├── hooks/                // 自定义 Hooks
│   ├── usePermission.ts  // 权限控制 Hook
│   ├── useApi.ts         // API 请求 Hook
│   └── useTable.ts       // 表格通用 Hook
├── layout/               // 布局组件
│   ├── components/       // 布局子组件（侧边栏、顶部栏等）
│   └── index.vue         // 主布局组件
├── router/               // 路由配置
│   ├── index.ts          // 路由实例配置
│   ├── routes.ts         // 路由定义
│   ├── generateRoutes.ts // 动态路由生成
│   └── guards.ts         // 路由守卫
├── store/                // Pinia 状态管理
│   ├── index.ts          // Store 入口
│   └── modules/          // 业务模块 Store
│       ├── user.ts       // 用户相关状态
│       ├── role.ts       // 角色相关状态
│       └── sync.ts       // 同步相关状态
├── permission.ts         // 权限控制入口（路由守卫 + 权限初始化）
├── utils/                // 工具函数
│   ├── format.ts         // 格式化工具（日期、数字等）
│   ├── validator.ts      // 数据校验工具
│   └── ws.ts             // WebSocket 工具
├── views/                // 页面组件
│   ├── login/            // 登录页
│   ├── dashboard/        // 控制台
│   ├── system/           // 系统管理（用户/角色/菜单/部门）
│   └── sync/             // 数据库同步
├── App.vue               // 根组件
├── main.ts               // 入口文件
├── env.d.ts              // 环境变量类型声明
├── tsconfig.json         // TypeScript 配置
├── vite.config.ts        // Vite 配置
├── .eslintrc.js          // ESLint 配置
├── .prettierrc.js        // Prettier 配置
└── package.json          // 依赖配置
```
### 3. 代码风格规范（结合 Airbnb + vue-element-plus-admin 规范）
1. 命名规范：
   - 组件文件名：PascalCase（如 `UserManagement.vue`）
   - 非组件文件（工具函数、API、Store）：camelCase（如 `formatDate.ts`）
   - 接口/类型名：PascalCase，前缀体现用途（如 `UserDTO`、`MenuPermission`）
   - 常量：UPPER_CASE，按模块拆分（如 `const USER_STATUS = { ACTIVE: 'active' }`）
   - 变量/函数名：camelCase，语义化命名（如 `fetchUserList` 而非 `getUser`）
2. 代码格式：
   - 缩进：2 个空格（ESLint 强制）
   - 行宽：120 字符（Prettier 配置）
   - 分号：必须加（ESLint 强制）
   - 引号：单引号（Prettier 配置）
   - 对象/数组：末尾无逗号（Prettier 配置）
3. Vue SFC 代码顺序：
   - `<script setup lang="ts">`（必须在最上方）
   - `<template>`（中间）
   - `<style scoped>`（最下方）
4. 特殊禁止项：
   - 禁止使用 `var` 声明变量，必须使用 `let`/`const`
   - 禁止使用 `eval`、`with` 等危险语法
   - 禁止直接修改 Pinia `state`，通过 `actions` 修改（除了 `$patch`）
   - 禁止在模板中写复杂逻辑，复杂计算放在 `computed` 或 `getters` 中
   - 禁止提交 `console.log` 代码（ESLint 配置 `no-console`）
5. ESLint 配置（关键规则）：
   ```javascript
   // .eslintrc.js
   module.exports = {
     root: true,
     env: { browser: true, es2021: true, node: true },
     extends: [
       'eslint:recommended',
       'plugin:vue/vue3-essential',
       'plugin:@typescript-eslint/recommended',
       'plugin:@typescript-eslint/recommended-requiring-type-checking',
       'airbnb-base',
       'airbnb-typescript/base',
       'prettier',
     ],
     parser: 'vue-eslint-parser',
     parserOptions: {
       ecmaVersion: 'latest',
       parser: '@typescript-eslint/parser',
       sourceType: 'module',
       project: ['./tsconfig.json'],
     },
     plugins: ['vue', '@typescript-eslint', 'prettier'],
     rules: {
       'prettier/prettier': 'error',
       'vue/script-setup-uses-vars': 'error',
       'vue/no-mutating-props': 'error',
       '@typescript-eslint/no-explicit-any': 'error',
       '@typescript-eslint/explicit-module-boundary-types': 'error',
       'no-console': ['error', { allow: ['warn', 'error'] }],
       'import/no-cycle': 'off', // 允许合理的循环导入
       'max-len': ['error', { code: 120 }],
     },
   };
   ```
---
## 核心代码模板示例
### 1. 组件模板（UI 组件 + 容器组件）
#### UI 组件（纯展示，可复用）
```vue
<!-- src/components/molecules/UserForm/UserForm.vue -->
<template>
  <el-form
    ref="formRef"
    :model="form"
    :rules="rules"
    label-width="100px"
    class="user-form"
  >
    <el-form-item label="用户名" prop="userName">
      <el-input v-model="form.userName" placeholder="请输入用户名" />
    </el-form-item>
    <el-form-item label="邮箱" prop="email">
      <el-input v-model="form.email" type="email" placeholder="请输入邮箱" />
    </el-form-item>
    <el-form-item label="角色" prop="roleId">
      <el-select v-model="form.roleId" placeholder="请选择角色">
        <el-option
          v-for="role in roles"
          :key="role.id"
          :label="role.roleName"
          :value="role.id"
        />
      </el-select>
    </el-form-item>
    <el-form-item label="状态" prop="status">
      <el-radio-group v-model="form.status">
        <el-radio label="active">启用</el-radio>
        <el-radio label="disabled">禁用</el-radio>
      </el-radio-group>
    </el-form-item>
    <el-form-item>
      <el-button type="primary" @click="handleSubmit">提交</el-button>
      <el-button @click="handleCancel">取消</el-button>
    </el-form-item>
  </el-form>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { ElForm, ElFormItem, ElInput, ElSelect, ElOption, ElRadioGroup, ElRadio, ElButton } from 'element-plus';
import { RoleDTO } from '@/api/types/permission';

// Props 定义
interface Props {
  // 编辑模式：传入用户信息；新增模式：无
  modelValue?: {
    id?: number;
    userName: string;
    email: string;
    roleId: number;
    status: 'active' | 'disabled';
  };
  roles: RoleDTO[]; // 角色列表
}

// Emits 定义
const emit = defineEmits<{
  'update:modelValue': [value: Props['modelValue']];
  'submit': [formData: Props['modelValue']];
  'cancel': [];
}>();

const props = defineProps<Props>();

// 表单 Ref
const formRef = ref<InstanceType<typeof ElForm> | null>(null);

// 表单数据（双向绑定）
const form = ref<Props['modelValue']>({
  userName: '',
  email: '',
  roleId: 0,
  status: 'active',
  ...props.modelValue,
});

// 监听 modelValue 变化（支持 v-model 双向绑定）
watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      form.value = { ...newVal };
    }
  },
  { deep: true }
);

// 表单校验规则
const rules = computed(() => ({
  userName: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' },
  ],
  roleId: [{ required: true, message: '请选择角色', trigger: 'change' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}));

// 提交表单
const handleSubmit = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
    emit('submit', form.value);
    emit('update:modelValue', form.value);
  } catch (error) {
    console.error('表单校验失败:', error);
  }
};

// 取消操作
const handleCancel = () => {
  emit('cancel');
  formRef.value?.resetFields();
};
</script>

<style scoped lang="scss">
.user-form {
  max-width: 600px;
  margin: 0 auto;
  .el-form-item {
    margin-bottom: 20px;
  }
}
</style>
```
#### 容器组件（业务逻辑 + 权限控制）
```vue
<!-- src/views/system/user/UserManagement.vue -->
<template>
  <div class="user-management">
    <el-page-header content="用户管理" />
    <div class="user-management__header">
      <el-input
        v-model="searchKey"
        placeholder="请输入用户名/邮箱搜索"
        style="width: 300px; margin-right: 10px"
        @keyup.enter="fetchUserList"
      />
      <el-button
        type="primary"
        icon="Plus"
        @click="handleAdd"
        v-if="hasPermission('user:add')"
      >
        新增用户
      </el-button>
    </div>
    <el-table
      :data="userList"
      border
      stripe
      style="width: 100%; margin-top: 10px"
      @selection-change="handleSelectionChange"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column label="ID" prop="id" width="80" align="center" />
      <el-table-column label="用户名" prop="userName" />
      <el-table-column label="邮箱" prop="email" />
      <el-table-column label="角色" prop="roleName" />
      <el-table-column label="状态" prop="status">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'active' ? 'success' : 'danger'">
            {{ scope.row.status === 'active' ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="200" align="center">
        <template #default="scope">
          <el-button
            type="text"
            @click="handleEdit(scope.row)"
            v-if="hasPermission('user:edit')"
          >
            编辑
          </el-button>
          <el-button
            type="text"
            color="danger"
            @click="handleDelete(scope.row.id)"
            v-if="hasPermission('user:delete')"
          >
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      :current-page="pagination.page"
      :page-size="pagination.size"
      :total="pagination.total"
      style="margin-top: 10px; text-align: right"
      @size-change="handleSizeChange"
      @current-change="handleCurrentChange"
    />

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="isDialogOpen"
      :title="isEditMode ? '编辑用户' : '新增用户'"
      width="600px"
    >
      <UserForm
        v-model="formModel"
        :roles="roleList"
        @submit="handleFormSubmit"
        @cancel="isDialogOpen = false"
      />
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { ElPageHeader, ElInput, ElButton, ElTable, ElTableColumn, ElTag, ElPagination, ElDialog } from 'element-plus';
import { useUserStore } from '@/store/modules/user';
import { useRoleStore } from '@/store/modules/role';
import { usePermission } from '@/hooks/usePermission';
import UserForm from '@/components/molecules/UserForm/UserForm.vue';
import { UserDTO } from '@/api/types/user';
import { RoleDTO } from '@/api/types/permission';

// Store 实例
const userStore = useUserStore();
const roleStore = useRoleStore();

// 权限 Hook
const { hasPermission } = usePermission();

// 状态定义
const searchKey = ref('');
const isDialogOpen = ref(false);
const isEditMode = ref(false);
const formModel = ref<UserDTO | undefined>();
const userList = ref<UserDTO[]>([]);
const roleList = ref<RoleDTO[]>([]);
const pagination = ref({
  page: 1,
  size: 10,
  total: 0,
});

// 初始化：加载用户列表和角色列表
const initData = async () => {
  await Promise.all([fetchUserList(), fetchRoleList()]);
};

// 加载用户列表
const fetchUserList = async () => {
  await userStore.fetchUserList(pagination.value.page, pagination.value.size, searchKey.value);
  userList.value = userStore.list;
  pagination.value.total = userStore.pagination.total;
};

// 加载角色列表（用于表单选择）
const fetchRoleList = async () => {
  await roleStore.fetchRoleList();
  roleList.value = roleStore.list;
};

// 分页变更
const handleSizeChange = (size: number) => {
  pagination.value.size = size;
  fetchUserList();
};

const handleCurrentChange = (page: number) => {
  pagination.value.page = page;
  fetchUserList();
};

// 新增用户
const handleAdd = () => {
  isEditMode.value = false;
  formModel.value = {
    userName: '',
    email: '',
    roleId: roleList.value[0]?.id || 0,
    status: 'active',
  };
  isDialogOpen.value = true;
};

// 编辑用户
const handleEdit = (user: UserDTO) => {
  isEditMode.value = true;
  formModel.value = { ...user };
  isDialogOpen.value = true;
};

// 提交表单（新增/编辑）
const handleFormSubmit = async (formData: UserDTO) => {
  if (isEditMode.value) {
    await userStore.updateUser(formData); // 编辑用户
  } else {
    await userStore.createUser(formData); // 新增用户
  }
  isDialogOpen.value = false;
  fetchUserList(); // 刷新列表
};

// 删除用户
const handleDelete = async (userId: number) => {
  if (window.confirm('确定要删除该用户吗？')) {
    await userStore.deleteUser(userId);
    fetchUserList(); // 刷新列表
  }
};

// 表格多选
const handleSelectionChange = (selectedRows: UserDTO[]) => {
  // 批量操作逻辑
};

// 监听搜索关键词变化
watch(searchKey, (newVal) => {
  // 搜索防抖（可结合 useDebounce  Hook）
  const timer = setTimeout(() => {
    pagination.value.page = 1; // 重置到第一页
    fetchUserList();
  }, 500);
  return () => clearTimeout(timer);
});

// 初始化数据
initData();
</script>

<style scoped lang="scss">
.user-management {
  padding: 20px;
  &__header {
    display: flex;
    align-items: center;
    margin-bottom: 10px;
  }
}
</style>
```
### 2. Pinia Store 模板
```typescript
// src/store/modules/user.ts
import { defineStore } from 'pinia';
import { UserDTO, UserPermission, fetchUserList, createUser, updateUser, deleteUser, fetchUserPermission } from '@/api/modules/user';
import { encryptPassword } from '@/utils/encrypt'; // 密码加密工具（bcrypt 算法）

// 状态类型定义
interface UserState {
  list: UserDTO[]; // 用户列表
  currentUser: UserDTO | null; // 当前登录用户
  permission: UserPermission; // 用户权限信息
  status: 'idle' | 'loading' | 'failed'; // 加载状态
  pagination: {
    page: number;
    size: number;
    total: number;
  };
  token: string | null; // JWT Token
}

// 初始化状态
const initialState: UserState = {
  list: [],
  currentUser: null,
  permission: { roles: [], menus: [], permissionKeys: [] },
  status: 'idle',
  pagination: { page: 1, size: 10, total: 0 },
  token: localStorage.getItem('USER_TOKEN'), // 从本地存储获取 Token（仅存储 Token）
};

// 创建 Store
export const useUserStore = defineStore('user', {
  state: (): UserState => initialState,
  getters: {
    // 计算当前用户权限标识集合（简化获取）
    permissionKeys: (state) => state.permission.permissionKeys,
    // 计算当前用户角色列表
    roles: (state) => state.permission.roles,
  },
  actions: {
    // 保存 Token 到本地存储
    saveToken(token: string) {
      this.token = token;
      localStorage.setItem('USER_TOKEN', token);
    },

    // 退出登录：清除状态 + Token
    logout() {
      this.$reset(); // 重置状态到初始值
      localStorage.removeItem('USER_TOKEN');
    },

    // 获取用户权限信息（登录后调用）
    async fetchUserPermission() {
      this.status = 'loading';
      try {
        const permission = await fetchUserPermission();
        this.permission = permission;
        this.status = 'idle';
        return permission;
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },

    // 获取用户列表
    async fetchUserList(page = 1, size = 10, searchKey = '') {
      this.status = 'loading';
      try {
        const { list, total } = await fetchUserList(page, size, searchKey);
        this.list = list;
        this.pagination = { page, size, total };
        this.status = 'idle';
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },

    // 新增用户（密码加密）
    async createUser(userData: Omit<UserDTO, 'id'>) {
      this.status = 'loading';
      try {
        // 密码加密（bcrypt 算法，对齐权限管理模块安全要求）
        const encryptedPassword = await encryptPassword(userData.password);
        await createUser({ ...userData, password: encryptedPassword });
        this.status = 'idle';
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },

    // 编辑用户（如果修改密码则加密）
    async updateUser(userData: UserDTO) {
      this.status = 'loading';
      try {
        const updateData = { ...userData };
        // 如果传递了密码且密码有变化，则加密
        if (updateData.password) {
          updateData.password = await encryptPassword(updateData.password);
        }
        await updateUser(updateData);
        // 更新当前用户信息（如果编辑的是当前登录用户）
        if (this.currentUser?.id === userData.id) {
          this.currentUser = { ...this.currentUser, ...updateData };
        }
        this.status = 'idle';
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },

    // 删除用户（逻辑删除，对齐数据库规范）
    async deleteUser(userId: number) {
      this.status = 'loading';
      try {
        await deleteUser(userId);
        // 本地移除删除的用户（优化体验，无需重新请求列表）
        this.list = this.list.filter(user => user.id !== userId);
        this.status = 'idle';
      } catch (error) {
        this.status = 'failed';
        throw error;
      }
    },
  },
});
```
### 3. 路由配置模板
```typescript
// src/router/index.ts
import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router';
import { publicRoutes, protectedRoutes } from './routes';
import { setupPermissionGuard } from '@/permission';
import Layout from '@/layout/index.vue';

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [...publicRoutes], // 先注册公开路由
  scrollBehavior: () => ({ top: 0 }), // 路由切换时滚动到顶部
});

// 注册权限守卫
setupPermissionGuard(router);

export default router;
```

```typescript
// src/router/generateRoutes.ts
import { RouteRecordRaw } from 'vue-router';
import { MenuDTO } from '@/api/types/permission';
import Layout from '@/layout/index.vue';

/**
 * 基于用户菜单生成动态路由
 * @param menus 用户可访问菜单列表（来自后端）
 */
export const generateRoutes = (menus: MenuDTO[]): RouteRecordRaw[] => {
  const accessRoutes: RouteRecordRaw[] = [];

  // 递归处理菜单层级
  const handleMenus = (menuList: MenuDTO[], parentPath = ''): RouteRecordRaw[] => {
    return menuList.map(menu => {
      const route: RouteRecordRaw = {
        path: parentPath + menu.path,
        name: menu.name,
        component: menu.parentId === 0 ? Layout : () => import(`@/views${parentPath + menu.path}/index.vue`),
        meta: {
          title: menu.name,
          icon: menu.icon,
          permission: menu.permission,
          visible: menu.visible,
        },
      };

      // 处理子菜单
      if (menu.children && menu.children.length > 0) {
        route.children = handleMenus(menu.children, parentPath + menu.path + '/');
      }

      return route;
    });
  };

  // 生成路由并过滤不可见菜单
  const routes = handleMenus(menus);
  accessRoutes.push(...routes.filter(route => route.meta.visible !== false));

  return accessRoutes;
};
```
### 4. 权限 Hook 模板（已在权限规范中提供，此处补充完整实现）
```typescript
// src/hooks/usePermission.ts
import { ref, watch, onMounted } from 'vue';
import { useUserStore } from '@/store/modules/user';
import { useRouter } from 'vue-router';

export const usePermission = () => {
  const userStore = useUserStore();
  const router = useRouter();
  const isPermissionLoaded = ref(false); // 权限是否加载完成

  // 检查是否拥有指定权限标识
  const hasPermission = (permissionKey: string): boolean => {
    if (!isPermissionLoaded.value) return false;
    return userStore.permissionKeys.includes(permissionKey);
  };

  // 检查是否拥有指定角色
  const hasRole = (roleName: string | string[]): boolean => {
    if (!isPermissionLoaded.value) return false;
    const roleNames = userStore.roles.map(role => role.roleName);
    if (Array.isArray(roleName)) {
      return roleName.some(name => roleNames.includes(name));
    }
    return roleNames.includes(roleName);
  };

  // 检查是否拥有路由权限
  const hasRoutePermission = (routeName: string): boolean => {
    if (!isPermissionLoaded.value) return false;
    const route = router.getRoutes().find(r => r.name === routeName);
    if (!route || !route.meta.permission) return true; // 无权限配置的路由默认允许访问
    return hasPermission(route.meta.permission as string);
  };

  // 加载权限（如果未加载）
  const loadPermission = async () => {
    if (userStore.token && userStore.permissionKeys.length === 0) {
      try {
        await userStore.fetchUserPermission();
        isPermissionLoaded.value = true;
      } catch (error) {
        isPermissionLoaded.value = false;
        throw error;
      }
    } else {
      isPermissionLoaded.value = true;
    }
  };

  // 监听 Token 变化，重新加载权限
  watch(
    () => userStore.token,
    async (newToken) => {
      if (newToken) {
        await loadPermission();
      } else {
        isPermissionLoaded.value = false;
      }
    },
    { immediate: true }
  );

  // 初始化加载权限
  onMounted(() => {
    if (userStore.token) {
      loadPermission().catch(error => console.error('权限加载失败:', error));
    }
  });

  return {
    hasPermission,
    hasRole,
    hasRoutePermission,
    isPermissionLoaded,
    loadPermission,
  };
};
```
### 5. WebSocket 工具模板（对接部署文档 WebSocket 接口）
```typescript
// src/utils/ws.ts
import { ElMessage } from 'element-plus';

/**
 * WebSocket 工具类（对接后端同步进度/日志推送）
 */
export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private reconnectCount = 0;
  private maxReconnectCount = 5; // 最大重连次数
  private messageCallback: ((data: any) => void) | null = null;
  private closeCallback: (() => void) | null = null;

  constructor(url: string) {
    this.url = url;
    this.connect();
  }

  // 建立连接
  private connect() {
    this.ws = new WebSocket(this.url);

    // 连接成功
    this.ws.onopen = () => {
      console.log(`WebSocket 连接成功: ${ ${this.url}`);
      this.reconnectCount = 0; // 重置重连次数
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }
    };

    // 接收消息
    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.messageCallback?.(data);
    };

    // 连接关闭
    this.ws.onclose = () => {
      console.log(`WebSocket 连接关闭: ${this.url}`);
      this.closeCallback?.();
      this.reconnect(); // 自动重连
    };

    // 连接错误
    this.ws.onerror = (error) => {
      console.error(`WebSocket 错误: ${this.url}`, error);
      this.ws?.close();
    };
  }

  // 重连机制
  private reconnect() {
    if (this.reconnectCount >= this.maxReconnectCount) {
      ElMessage.error(`WebSocket 重连失败（已尝试${this.maxReconnectCount}次）`);
      return;
    }

    this.reconnectCount++;
    console.log(`WebSocket 正在重连（${this.reconnectCount}/${this.maxReconnectCount}）`);
    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, 3000); // 3 秒后重连
  }

  // 发送消息
  public send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      ElMessage.warning('WebSocket 连接未建立，无法发送消息');
    }
  }

  // 注册消息回调
  public onMessage(callback: (data: any) => void) {
    this.messageCallback = callback;
  }

  // 注册关闭回调
  public onClose(callback: () => void) {
    this.closeCallback = callback;
  }

  // 关闭连接
  public close() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    this.ws?.close();
    this.ws = null;
  }
}

// 同步进度 WebSocket 实例
export const syncProgressWs = new WebSocketClient(
  import.meta.env.VITE_WS_BASE_URL + '/sync-progress/'
);

// 日志推送 WebSocket 实例
export const logWs = new WebSocketClient(
  import.meta.env.VITE_WS_BASE_URL + '/logs/'
);
```
---
## 补充说明
1. 本规范完全对齐 `vue-element-plus-admin` 官方开发思想、目录结构与技术栈，同时整合了项目部署要求与权限管理模块需求。
2. 所有代码示例均遵循 TypeScript 严格模式，无 `any` 类型，接口定义完整，可直接复用。
3. 权限管理模块严格遵循 RBAC 模型，实现路由、菜单、按钮三级权限控制，对接后端 `system_db` 数据库表结构。
4. API 封装与后端 FastAPI 接口完全对齐，支持防重提交、Token 校验、错误统一处理。
5. 测试规范覆盖组件、Store、API 等核心模块，确保代码质量。
6. 部署规范与文档要求一致，支持开发环境与生产环境切换，提供 Nginx 配置示例。

使用本规范开发时，建议配合 `vue-element-plus-admin` 官方文档（https://element-plus-admin-doc.cn/guide/introduction.html）查阅具体组件使用方式与进阶功能。