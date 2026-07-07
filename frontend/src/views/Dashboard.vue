<template>
  <div class="screening-workbench">
    <section class="workbench-hero">
      <div>
        <p class="hero-eyebrow">岗位初筛</p>
        <h1>岗位初筛工作台</h1>
        <p class="hero-subtitle">
          请选择一个历史岗位开始筛选，或新建岗位 JD 后保存到岗位库。
        </p>
      </div>
      <div class="hero-actions">
        <el-button size="large" @click="openTaskHistory">
          <el-icon><Clock /></el-icon>
          历史初筛任务
        </el-button>
      </div>
    </section>

    <section class="steps-panel">
      <el-steps :active="activeStep" finish-status="success" align-center>
        <el-step title="选择岗位 / 新建岗位" />
        <el-step title="上传简历" />
        <el-step title="开始初筛" />
      </el-steps>
    </section>

    <section v-if="activeStep === 0" class="setup-grid">
      <div class="panel position-panel">
        <div class="panel-header">
          <div>
            <h2>选择招聘岗位</h2>
            <p>优先使用历史岗位，减少重复录入。</p>
          </div>
          <el-button type="primary" @click="openCreatePosition">
            <el-icon><Plus /></el-icon>
            新建岗位 JD
          </el-button>
        </div>

        <div class="filter-row">
          <el-input
            v-model="positionFilters.keyword"
            clearable
            placeholder="搜索岗位名称 / 岗位类型 / 部门"
            @keyup.enter="fetchJobPositions"
            @clear="fetchJobPositions"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="positionFilters.positionType"
            clearable
            placeholder="岗位类型"
            @change="fetchJobPositions"
            @clear="fetchJobPositions"
          >
            <el-option
              v-for="type in positionTypeOptions"
              :key="type"
              :label="type"
              :value="type"
            />
          </el-select>
          <el-button @click="fetchJobPositions">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <el-alert
          v-if="positionLoadError"
          class="load-alert"
          type="error"
          :closable="false"
          show-icon
          title="岗位列表加载失败"
          :description="positionLoadError"
        >
          <template #default>
            <el-button size="small" @click="fetchJobPositions">重试</el-button>
          </template>
        </el-alert>

        <div v-loading="positionLoading" class="position-list">
          <el-empty
            v-if="!positionLoading && positionList.length === 0"
            description="暂无岗位，请先新建岗位 JD"
          >
            <el-button type="primary" @click="openCreatePosition">
              <el-icon><Plus /></el-icon>
              新建岗位 JD
            </el-button>
          </el-empty>

          <article
            v-for="position in positionList"
            :key="position.id"
            class="position-card"
            :class="{ selected: isSelectedPosition(position) }"
            @click="selectPosition(position)"
          >
            <div class="position-card-main">
              <div class="position-title-line">
                <h3>{{ position.position_name }}</h3>
                <el-tag size="small" effect="light">{{ position.position_type || '其他' }}</el-tag>
              </div>
              <p class="position-meta">
                {{ position.position_type || '其他' }}｜{{ position.education_requirement || '学历不限' }}｜{{ position.experience_requirement || '不限经验' }}
              </p>
              <div class="position-foot">
                <span>最近使用：{{ formatRelativeTime(position.last_used_time) }}</span>
                <span>已筛选：{{ position.candidate_count || 0 }}人</span>
              </div>
            </div>
            <el-dropdown trigger="click" @click.stop>
              <el-button text class="card-more">
                <el-icon><MoreFilled /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="openEditPosition(position)">编辑岗位信息</el-dropdown-item>
                  <el-dropdown-item @click="copyPosition(position)">复制岗位</el-dropdown-item>
                  <el-dropdown-item divided @click="archivePosition(position)">归档岗位</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </article>
        </div>
      </div>

      <div class="panel summary-panel">
        <div class="panel-header">
          <div>
            <h2>岗位信息摘要</h2>
            <p>确认岗位要求后再上传简历。</p>
          </div>
        </div>

        <div v-if="!selectedPosition" class="position-empty">
          <el-icon><Briefcase /></el-icon>
          <h3>请选择一个历史岗位</h3>
          <p>选择后系统会展示岗位要求、筛选重点和淘汰规则。</p>
        </div>

        <div v-else class="summary-content">
          <div class="summary-title">
            <div>
              <h3>{{ selectedPosition.position_name }}</h3>
              <p>{{ selectedPosition.department_name || '未分配部门' }}</p>
            </div>
            <el-tag type="success" effect="light">V{{ selectedPosition.version || 1 }}</el-tag>
          </div>

          <div class="summary-fields">
            <div>
              <span>岗位类型</span>
              <strong>{{ selectedPosition.position_type || '其他' }}</strong>
            </div>
            <div>
              <span>学历要求</span>
              <strong>{{ selectedPosition.education_requirement || '不限' }}</strong>
            </div>
            <div>
              <span>经验要求</span>
              <strong>{{ selectedPosition.experience_requirement || '不限' }}</strong>
            </div>
            <div>
              <span>已筛选候选人</span>
              <strong>{{ selectedPosition.candidate_count || 0 }} 人</strong>
            </div>
          </div>

          <div class="summary-section">
            <h4>核心筛选点</h4>
            <ol>
              <li v-for="item in listForDisplay(selectedPosition.screening_rules, 5)" :key="item">{{ item }}</li>
            </ol>
            <p v-if="listForDisplay(selectedPosition.screening_rules).length === 0" class="muted">暂无核心筛选点</p>
          </div>

          <div class="summary-section">
            <h4>必备条件</h4>
            <ol>
              <li v-for="item in listForDisplay(selectedPosition.must_have, 5)" :key="item">{{ item }}</li>
            </ol>
            <p v-if="listForDisplay(selectedPosition.must_have).length === 0" class="muted">暂无必备条件</p>
          </div>

          <div class="summary-section">
            <h4>加分项</h4>
            <ol>
              <li v-for="item in listForDisplay(selectedPosition.nice_to_have, 5)" :key="item">{{ item }}</li>
            </ol>
            <p v-if="listForDisplay(selectedPosition.nice_to_have).length === 0" class="muted">暂无加分项</p>
          </div>

          <div class="summary-section risk">
            <h4>淘汰风险</h4>
            <ol>
              <li v-for="item in listForDisplay(selectedPosition.risk_points, 5)" :key="item">{{ item }}</li>
            </ol>
            <p v-if="listForDisplay(selectedPosition.risk_points).length === 0" class="muted">暂无淘汰风险</p>
          </div>

          <div class="summary-actions">
            <el-button size="large" @click="openEditPosition(selectedPosition)">
              <el-icon><Edit /></el-icon>
              编辑岗位信息
            </el-button>
            <el-button type="primary" size="large" @click="useSelectedPosition">
              使用此岗位开始初筛
              <el-icon><ArrowRight /></el-icon>
            </el-button>
          </div>
        </div>
      </div>
    </section>

    <section v-if="activeStep === 1" class="panel upload-panel">
      <div class="panel-header">
        <div>
          <h2>批量上传简历</h2>
          <p>岗位：{{ selectedPosition?.position_name }}。支持 PDF / DOC / DOCX。</p>
        </div>
        <el-button @click="activeStep = 0">重新选择岗位</el-button>
      </div>

      <el-upload
        class="resume-uploader"
        drag
        multiple
        accept=".pdf,.doc,.docx"
        :auto-upload="false"
        :file-list="resumeUploadList"
        :on-change="handleResumeFileChange"
        :on-remove="handleResumeFileRemove"
        :before-upload="beforeResumeUpload"
      >
        <el-icon class="upload-icon"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽简历到此处，或<em>点击选择文件</em>
        </div>
        <template #tip>
          <div class="upload-tip">系统会逐份解析和初筛，避免多份简历一次性 AI 调用导致超时。</div>
        </template>
      </el-upload>

      <div class="file-list-card">
        <div class="file-list-title">
          <h3>文件列表</h3>
          <span>{{ resumeQueue.length }} 份简历</span>
        </div>
        <el-table :data="resumeQueue" empty-text="请先上传简历文件">
          <el-table-column prop="name" label="文件名" min-width="260" />
          <el-table-column label="大小" width="120">
            <template #default="{ row }">{{ formatFileSize(row.size) }}</template>
          </el-table-column>
          <el-table-column label="上传状态" width="130">
            <template #default="{ row }">
              <el-tag :type="uploadStatusType(row.status)" effect="light">{{ uploadStatusText(row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="解析状态" width="150">
            <template #default="{ row }">
              <el-tag :type="parseStatusType(row.parse_status)" effect="light">{{ parseStatusText(row.parse_status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="说明" min-width="180">
            <template #default="{ row }">
              <span class="muted">{{ row.error || '等待处理' }}</span>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div class="step-actions">
        <el-button size="large" @click="activeStep = 0">上一步</el-button>
        <el-button type="primary" size="large" :disabled="resumeQueue.length === 0" @click="activeStep = 2">
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
      </div>
    </section>

    <section v-if="activeStep === 2" class="panel confirm-panel">
      <div class="panel-header">
        <div>
          <h2>确认并开始初筛</h2>
          <p>系统会按简历逐份执行 JD 解析、简历解析、匹配度计算和结果生成。</p>
        </div>
      </div>

      <div class="task-summary-grid">
        <div>
          <span>JD 状态</span>
          <strong>{{ selectedPosition || activeTask ? '已选择岗位库 JD' : '未选择' }}</strong>
        </div>
        <div>
          <span>简历数量</span>
          <strong>{{ progress.total || resumeQueue.length }}</strong>
        </div>
        <div>
          <span>解析成功数量</span>
          <strong>{{ progress.parsed_success }}</strong>
        </div>
        <div>
          <span>解析失败数量</span>
          <strong>{{ progress.parsed_failed }}</strong>
        </div>
        <div>
          <span>当前阶段</span>
          <strong>{{ currentStage }}</strong>
        </div>
      </div>

      <div class="screening-flow">
        <FlowStepCard
          v-for="step in screeningSteps"
          :key="step.title"
          :index="step.index"
          :title="step.title"
          :desc="step.desc"
          :status="step.status"
        />
      </div>

      <el-progress
        v-if="screeningRunning || progress.total > 0"
        :percentage="screeningPercentage"
        :status="screeningPercentage >= 100 ? 'success' : undefined"
      />

      <div class="step-actions">
        <el-button size="large" :disabled="screeningRunning" @click="activeStep = 1">上一步</el-button>
        <el-button type="primary" size="large" :loading="screeningRunning" @click="startScreening">
          开始 AI 初筛
        </el-button>
      </div>
    </section>

    <section v-if="activeStep === 3" class="results-layout">
      <div class="panel result-panel">
        <div class="panel-header">
          <div>
            <h2>初筛结果页</h2>
            <p>已根据岗位库 JD 快照生成候选人推荐名单。</p>
          </div>
          <div class="result-actions">
            <el-button @click="resetWorkbench">
              <el-icon><RefreshLeft /></el-icon>
              新建初筛任务
            </el-button>
          </div>
        </div>

        <div class="result-stats">
          <div>
            <span>推荐面试</span>
            <strong>{{ progress.recommended }}</strong>
          </div>
          <div>
            <span>待复核</span>
            <strong>{{ progress.pending }}</strong>
          </div>
          <div>
            <span>不建议</span>
            <strong>{{ progress.rejected }}</strong>
          </div>
          <div>
            <span>处理完成</span>
            <strong>{{ progress.screened }}</strong>
          </div>
        </div>

        <el-table v-loading="resultLoading" :data="resultRows" empty-text="暂无初筛结果">
          <el-table-column prop="rank" label="排名" width="80" />
          <el-table-column label="候选人" min-width="180">
            <template #default="{ row }">
              <div class="candidate-cell">
                <strong>{{ row.candidate_name || row.file_name }}</strong>
                <span>{{ row.latest_position || row.city || '简历岗位未体现' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="score" label="匹配度" width="110">
            <template #default="{ row }">
              <strong v-if="row.score !== null && row.score !== undefined">{{ row.score }}</strong>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="conclusion_label" label="AI 结论" width="140" />
          <el-table-column label="来源" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="resultSourceType(row.result_source)" effect="light">
                {{ resultSourceText(row.result_source) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="优势" min-width="220">
            <template #default="{ row }">
              <div class="tag-line">
                <el-tag
                  v-for="item in listForDisplay(row.match_highlights, 2)"
                  :key="item"
                  size="small"
                  effect="light"
                >
                  {{ item }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="风险点" min-width="220">
            <template #default="{ row }">
              <div class="tag-line">
                <el-tag
                  v-for="item in listForDisplay(row.risk_points, 2)"
                  :key="item"
                  size="small"
                  type="warning"
                  effect="light"
                >
                  {{ item }}
                </el-tag>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="360" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" :disabled="!row.result_id" @click="openResultDetail(row)">
                查看详情
              </el-button>
              <el-button size="small" text :disabled="!row.result_id" @click="changeResultStatus(row, 'INTERVIEW')">
                约面
              </el-button>
              <el-button size="small" text type="warning" :disabled="!row.result_id" @click="changeResultStatus(row, 'PENDING')">
                待定
              </el-button>
              <el-button size="small" text type="danger" :disabled="!row.result_id" @click="changeResultStatus(row, 'REJECTED')">
                淘汰
              </el-button>
              <el-button size="small" text :loading="row.reprocessing" :disabled="!row.resume_file_id" @click="reprocessResult(row, false)">
                重新筛选
              </el-button>
              <el-button size="small" text type="warning" :loading="row.reprocessing" :disabled="!row.resume_file_id" @click="reprocessResult(row, true)">
                重新解析
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </section>

    <el-drawer v-model="detailDrawerVisible" title="候选人初筛详情" size="520px">
      <div v-if="selectedDetail" class="detail-drawer">
        <h3>{{ selectedDetail.candidate_profile?.name || selectedDetail.resume_file?.file_name }}</h3>
        <div class="detail-score">
          <span>匹配度</span>
          <strong>{{ selectedDetail.result?.score ?? '-' }}</strong>
        </div>
        <el-descriptions :column="1" border>
          <el-descriptions-item label="AI 结论">{{ selectedDetail.result?.conclusion || '-' }}</el-descriptions-item>
          <el-descriptions-item label="结果来源">{{ resultSourceText(selectedDetail.result?.result_source) }}</el-descriptions-item>
          <el-descriptions-item label="候选人">{{ selectedDetail.candidate_profile?.name || '-' }}</el-descriptions-item>
          <el-descriptions-item label="电话">{{ selectedDetail.candidate_profile?.phone || '-' }}</el-descriptions-item>
          <el-descriptions-item label="学历">{{ selectedDetail.candidate_profile?.education || '-' }}</el-descriptions-item>
          <el-descriptions-item label="工作年限">{{ selectedDetail.candidate_profile?.work_years || '-' }}</el-descriptions-item>
        </el-descriptions>
        <div class="detail-section">
          <h4>匹配优势</h4>
          <ul>
            <li v-for="item in listForDisplay(selectedDetail.result?.match_highlights, 6)" :key="item">{{ item }}</li>
          </ul>
        </div>
        <div class="detail-section">
          <h4>风险点</h4>
          <ul>
            <li v-for="item in listForDisplay(selectedDetail.result?.risk_points, 6)" :key="item">{{ item }}</li>
          </ul>
        </div>
      </div>
    </el-drawer>

    <el-drawer v-model="taskHistoryVisible" title="历史初筛任务" size="720px">
      <div class="task-history">
        <div class="history-filters">
          <el-input
            v-model="taskHistoryFilters.keyword"
            clearable
            placeholder="搜索任务名称 / 岗位 / 类型"
            @keyup.enter="fetchTaskHistory"
            @clear="fetchTaskHistory"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
          <el-select
            v-model="taskHistoryFilters.status"
            clearable
            placeholder="任务状态"
            @change="fetchTaskHistory"
            @clear="fetchTaskHistory"
          >
            <el-option
              v-for="item in taskStatusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button @click="fetchTaskHistory">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
        </div>

        <el-table
          v-loading="taskHistoryLoading"
          :data="taskHistoryRows"
          empty-text="暂无历史初筛任务"
        >
          <el-table-column label="任务" min-width="190">
            <template #default="{ row }">
              <div class="history-task-cell">
                <strong>{{ row.task_name || '岗位初筛任务' }}</strong>
                <span>{{ row.job_title || '未命名岗位' }}｜{{ row.job_type || '其他' }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag size="small" :type="taskStatusType(row.status)" effect="light">
                {{ taskStatusText(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="简历" width="90">
            <template #default="{ row }">
              {{ row.total_resume_count || 0 }} 份
            </template>
          </el-table-column>
          <el-table-column label="结果" min-width="150">
            <template #default="{ row }">
              <span class="history-result-text">
                推荐 {{ row.recommended_count || 0 }} / 待定 {{ row.pending_count || 0 }} / 淘汰 {{ row.rejected_count || 0 }}
              </span>
            </template>
          </el-table-column>
          <el-table-column label="更新时间" width="120">
            <template #default="{ row }">
              {{ formatDateTime(row.updated_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="{ row }">
              <el-button size="small" text type="primary" @click="openHistoryTask(row)">
                查看结果
              </el-button>
              <el-button
                v-if="canContinueHistoryTask(row)"
                size="small"
                text
                type="warning"
                :loading="screeningRunning && activeTask?.id === row.id"
                @click="continueHistoryTask(row)"
              >
                继续处理
              </el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="history-pagination">
          <el-pagination
            v-model:current-page="taskHistoryPagination.page"
            background
            small
            layout="prev, pager, next"
            :page-size="taskHistoryPagination.pageSize"
            :total="taskHistoryPagination.total"
            @current-change="fetchTaskHistory"
          />
        </div>
      </div>
    </el-drawer>

    <el-dialog
      v-model="positionDialogVisible"
      :title="positionDialogTitle"
      width="1040px"
      class="position-dialog"
      destroy-on-close
    >
      <div class="position-dialog-body">
        <div class="jd-input-panel">
          <h3>JD 输入方式</h3>
          <el-upload
            class="jd-file-upload"
            accept=".pdf,.doc,.docx,.txt"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="handlePositionJdFileChange"
          >
            <el-button>
              <el-icon><Upload /></el-icon>
              上传 JD 文件
            </el-button>
          </el-upload>
          <el-input
            v-model="positionForm.jd_original_text"
            type="textarea"
            :rows="14"
            resize="none"
            placeholder="粘贴岗位 JD 原文，系统会自动提取岗位名称、岗位类型、学历、经验和筛选重点。"
          />
          <el-button
            type="primary"
            :loading="positionParsing"
            :disabled="!positionForm.jd_original_text.trim()"
            @click="parsePositionJd"
          >
            <el-icon><MagicStick /></el-icon>
            自动生成岗位信息
          </el-button>
        </div>

        <div class="position-form-panel">
          <h3>岗位信息</h3>
          <el-form label-position="top" class="position-form">
            <div class="form-grid">
              <el-form-item label="岗位名称" required>
                <el-input v-model="positionForm.position_name" placeholder="例如：销售代表" />
              </el-form-item>
              <el-form-item label="岗位类型">
                <el-select v-model="positionForm.position_type" allow-create filterable placeholder="选择或输入岗位类型">
                  <el-option v-for="type in positionTypeOptions" :key="type" :label="type" :value="type" />
                </el-select>
              </el-form-item>
              <el-form-item label="部门名称">
                <el-input v-model="positionForm.department_name" placeholder="例如：销售部" />
              </el-form-item>
              <el-form-item label="学历要求">
                <el-input v-model="positionForm.education_requirement" placeholder="例如：大专及以上" />
              </el-form-item>
              <el-form-item label="经验要求">
                <el-input v-model="positionForm.experience_requirement" placeholder="例如：1-3年" />
              </el-form-item>
            </div>

            <el-form-item label="岗位职责">
              <el-input v-model="positionForm.responsibilities_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="任职要求">
              <el-input v-model="positionForm.requirements_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="核心筛选点">
              <el-input v-model="positionForm.screening_rules_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="必备条件">
              <el-input v-model="positionForm.must_have_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="加分项">
              <el-input v-model="positionForm.nice_to_have_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="淘汰风险">
              <el-input v-model="positionForm.risk_points_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
            <el-form-item label="面试建议问题">
              <el-input v-model="positionForm.interview_questions_text" type="textarea" :rows="3" placeholder="一行一条" />
            </el-form-item>
          </el-form>
        </div>
      </div>

      <template #footer>
        <el-button @click="positionDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="positionSaving" @click="savePosition">
          保存到岗位库
        </el-button>
      </template>
    </el-dialog>

    <!-- AI 处理遮罩 -->
    <AiProcessingOverlay
      :visible="aiOverlayVisible"
      :title="aiOverlayTitle"
      :stages="aiOverlayStages"
      :progress="aiOverlayProgress"
      :hint="aiOverlayHint"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowRight,
  Briefcase,
  Clock,
  Edit,
  MagicStick,
  MoreFilled,
  Plus,
  RefreshLeft,
  Search,
  Upload,
  UploadFilled
} from '@element-plus/icons-vue'
import { jobPositionsApi, screeningApi } from '../api/analysis.js'
import AiProcessingOverlay from '../components/AiProcessingOverlay.vue'
import FlowStepCard from '../components/FlowStepCard.vue'

const positionTypeOptions = ['销售', '业务', '行政', '客服', '运营', '财务', '其他']

// AI 处理遮罩状态
const aiOverlayVisible = ref(false)
const aiOverlayTitle = ref('AI 正在分析')
const aiOverlayStages = ref([])
const aiOverlayProgress = ref(0)
const aiOverlayHint = ref('')

const activeStep = ref(0)
const positionLoading = ref(false)
const positionLoadError = ref('')
const positionList = ref([])
const selectedPosition = ref(null)
const positionFilters = reactive({
  keyword: '',
  positionType: ''
})

const positionDialogVisible = ref(false)
const positionDialogMode = ref('create')
const editingPosition = ref(null)
const positionParsing = ref(false)
const positionSaving = ref(false)

const createEmptyPositionForm = () => ({
  position_name: '',
  position_type: '',
  department_name: '',
  education_requirement: '',
  experience_requirement: '',
  jd_original_text: '',
  jd_structured_json: {},
  responsibilities_text: '',
  requirements_text: '',
  screening_rules_text: '',
  must_have_text: '',
  nice_to_have_text: '',
  risk_points_text: '',
  interview_questions_text: ''
})

const positionForm = reactive(createEmptyPositionForm())

const resumeUploadList = ref([])
const resumeQueue = ref([])
const activeTask = ref(null)
const screeningRunning = ref(false)
const resultLoading = ref(false)
const resultRows = ref([])
const currentStage = ref('待开始')
const progress = reactive({
  status: 'DRAFT',
  total: 0,
  parsed_success: 0,
  parsed_failed: 0,
  screened: 0,
  recommended: 0,
  pending: 0,
  rejected: 0
})

const detailDrawerVisible = ref(false)
const selectedDetail = ref(null)

const taskHistoryVisible = ref(false)
const taskHistoryLoading = ref(false)
const taskHistoryRows = ref([])
const taskHistoryFilters = reactive({
  keyword: '',
  status: ''
})
const taskHistoryPagination = reactive({
  page: 1,
  pageSize: 10,
  total: 0
})
const taskStatusOptions = [
  { value: 'DRAFT', label: '草稿' },
  { value: 'READY', label: '待初筛' },
  { value: 'SCREENING', label: '初筛中' },
  { value: 'COMPLETED', label: '已完成' },
  { value: 'FAILED', label: '处理失败' }
]

const positionDialogTitle = computed(() => (
  positionDialogMode.value === 'edit' ? '编辑岗位信息' : '新建岗位 JD'
))

const screeningPercentage = computed(() => {
  const total = progress.total || resumeQueue.value.length
  if (!total) return 0
  const handled = (progress.parsed_success || 0) + (progress.parsed_failed || 0)
  return Math.min(100, Math.round((handled / total) * 100))
})

const screeningSteps = computed(() => {
  const done = activeStep.value === 3
  const hasTaskJd = Boolean(selectedPosition.value || activeTask.value)
  const parsedAny = progress.parsed_success + progress.parsed_failed > 0
  const screenedAny = progress.screened > 0

  // 计算当前激活步骤：第一个未完成的步骤
  let activeIndex = 0
  if (!hasTaskJd) activeIndex = 1
  else if (!parsedAny) activeIndex = 2
  else if (!screenedAny) activeIndex = 3
  else if (!done) activeIndex = 5
  else activeIndex = 0 // 全部完成，无 active

  return [
    {
      index: 1,
      title: 'JD 解析',
      desc: hasTaskJd ? '使用岗位库当前版本和任务快照' : '等待岗位信息',
      status: hasTaskJd ? 'done' : (activeIndex === 1 && screeningRunning.value ? 'active' : 'pending')
    },
    {
      index: 2,
      title: '简历解析',
      desc: '逐份提取候选人基础信息',
      status: parsedAny ? 'done' : (activeIndex === 2 && screeningRunning.value ? 'active' : 'pending')
    },
    {
      index: 3,
      title: '候选人信息提取',
      desc: '形成可复核的候选人结构化资料',
      status: screenedAny ? 'done' : (activeIndex === 3 && screeningRunning.value ? 'active' : 'pending')
    },
    {
      index: 4,
      title: '岗位匹配度计算',
      desc: '基于岗位规则、风险点和简历内容评分',
      status: screenedAny ? 'done' : (activeIndex === 4 && screeningRunning.value ? 'active' : 'pending')
    },
    {
      index: 5,
      title: '生成初筛结果',
      desc: '输出推荐面试、待复核和淘汰建议',
      status: done ? 'done' : (activeIndex === 5 && screeningRunning.value ? 'active' : 'pending')
    }
  ]
})

const resetPositionForm = () => {
  Object.assign(positionForm, createEmptyPositionForm())
}

const getErrorMessage = (error, fallback) => {
  const detail = error?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg || JSON.stringify(item)).join('；')
  return fallback
}

const normalizeList = (value) => {
  if (!value) return []
  if (Array.isArray(value)) {
    return value
      .map((item) => {
        if (item === null || item === undefined) return ''
        if (typeof item === 'string') return item
        return item.question || item.content || item.name || item.title || JSON.stringify(item)
      })
      .map((item) => String(item).trim())
      .filter(Boolean)
  }
  if (typeof value === 'string') {
    return value
      .split(/\r?\n|；|;/)
      .map((item) => item.trim())
      .filter(Boolean)
  }
  return []
}

const listForDisplay = (value, limit) => {
  const list = normalizeList(value)
  return typeof limit === 'number' ? list.slice(0, limit) : list
}

const listToText = (value) => normalizeList(value).join('\n')

const textToList = (value) => normalizeList(value)

const fillPositionForm = (data = {}) => {
  const structured = data.jd_structured_json || data.parsed_jd || {}
  positionForm.position_name = data.position_name || structured.job_title || structured.job_name || ''
  positionForm.position_type = data.position_type || structured.job_type || ''
  positionForm.department_name = data.department_name || structured.department_name || structured.department || ''
  positionForm.education_requirement = data.education_requirement || structured.education_requirement || structured.education_req || ''
  positionForm.experience_requirement = data.experience_requirement || structured.experience_requirement || structured.experience_req || ''
  positionForm.jd_original_text = data.jd_original_text || data.jd_text || ''
  positionForm.jd_structured_json = structured
  positionForm.responsibilities_text = listToText(structured.responsibilities || structured.job_responsibilities)
  positionForm.requirements_text = listToText(structured.requirements || structured.job_requirements)
  positionForm.screening_rules_text = listToText(data.screening_rules || structured.key_screening_points || structured.resume_screening_dimensions)
  positionForm.must_have_text = listToText(data.must_have || structured.must_have || structured.must_have_skills || structured.must_have_conditions)
  positionForm.nice_to_have_text = listToText(data.nice_to_have || structured.nice_to_have || structured.nice_to_have_skills || structured.nice_to_have_conditions)
  positionForm.risk_points_text = listToText(data.risk_points || structured.risk_points || structured.reject_conditions || structured.deal_breakers)
  positionForm.interview_questions_text = listToText(data.interview_questions || structured.interview_questions || structured.suggested_interview_questions)
}

/** 渐进填充表单（AI 自动生成时使用，逐字段动画填充） */
const fillPositionFormAnimated = async (data = {}) => {
  const structured = data.jd_structured_json || data.parsed_jd || {}

  const fields = [
    { key: 'position_name', value: data.position_name || structured.job_title || structured.job_name || '' },
    { key: 'position_type', value: data.position_type || structured.job_type || '' },
    { key: 'department_name', value: data.department_name || structured.department_name || structured.department || '' },
    { key: 'education_requirement', value: data.education_requirement || structured.education_requirement || structured.education_req || '' },
    { key: 'experience_requirement', value: data.experience_requirement || structured.experience_requirement || structured.experience_req || '' }
  ]

  // 先填充基本字段（逐个带延迟）
  for (let i = 0; i < fields.length; i++) {
    if (fields[i].value) {
      positionForm[fields[i].key] = fields[i].value
    }
    await delay(120)
  }

  // 文本类字段依次填充
  const jdOriginalText = data.jd_original_text || data.jd_text || ''
  if (jdOriginalText) {
    positionForm.jd_original_text = jdOriginalText
  }
  positionForm.jd_structured_json = structured

  const textFields = [
    { key: 'responsibilities_text', value: listToText(structured.responsibilities || structured.job_responsibilities) },
    { key: 'requirements_text', value: listToText(structured.requirements || structured.job_requirements) },
    { key: 'screening_rules_text', value: listToText(data.screening_rules || structured.key_screening_points || structured.resume_screening_dimensions) },
    { key: 'must_have_text', value: listToText(data.must_have || structured.must_have || structured.must_have_skills || structured.must_have_conditions) },
    { key: 'nice_to_have_text', value: listToText(data.nice_to_have || structured.nice_to_have || structured.nice_to_have_skills || structured.nice_to_have_conditions) },
    { key: 'risk_points_text', value: listToText(data.risk_points || structured.risk_points || structured.reject_conditions || structured.deal_breakers) },
    { key: 'interview_questions_text', value: listToText(data.interview_questions || structured.interview_questions || structured.suggested_interview_questions) }
  ]

  for (let i = 0; i < textFields.length; i++) {
    positionForm[textFields[i].key] = textFields[i].value
    await delay(150)
  }
}

/** 简单延迟工具 */
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms))

const buildStructuredJd = () => ({
  ...(positionForm.jd_structured_json || {}),
  job_title: positionForm.position_name,
  job_type: positionForm.position_type,
  department_name: positionForm.department_name,
  education_requirement: positionForm.education_requirement,
  experience_requirement: positionForm.experience_requirement,
  responsibilities: textToList(positionForm.responsibilities_text),
  requirements: textToList(positionForm.requirements_text),
  key_screening_points: textToList(positionForm.screening_rules_text),
  must_have: textToList(positionForm.must_have_text),
  nice_to_have: textToList(positionForm.nice_to_have_text),
  risk_points: textToList(positionForm.risk_points_text),
  interview_questions: textToList(positionForm.interview_questions_text)
})

const buildPositionPayload = (saveMode) => ({
  position_name: positionForm.position_name.trim(),
  position_type: positionForm.position_type || '其他',
  department_name: positionForm.department_name || '未分配',
  education_requirement: positionForm.education_requirement || '',
  experience_requirement: positionForm.experience_requirement || '',
  jd_original_text: positionForm.jd_original_text.trim(),
  jd_structured_json: buildStructuredJd(),
  screening_rules: textToList(positionForm.screening_rules_text),
  must_have: textToList(positionForm.must_have_text),
  nice_to_have: textToList(positionForm.nice_to_have_text),
  risk_points: textToList(positionForm.risk_points_text),
  interview_questions: textToList(positionForm.interview_questions_text),
  ...(saveMode ? { save_mode: saveMode } : {})
})

const fetchJobPositions = async () => {
  positionLoading.value = true
  positionLoadError.value = ''
  try {
    const response = await jobPositionsApi.list({
      keyword: positionFilters.keyword || undefined,
      positionType: positionFilters.positionType || undefined,
      status: 'ACTIVE',
      page: 1,
      pageSize: 50
    })
    positionList.value = response.data.items || []
  } catch (error) {
    positionLoadError.value = getErrorMessage(error, '请稍后重试')
  } finally {
    positionLoading.value = false
  }
}

const openTaskHistory = () => {
  taskHistoryVisible.value = true
  taskHistoryPagination.page = 1
  fetchTaskHistory()
}

const fetchTaskHistory = async () => {
  taskHistoryLoading.value = true
  try {
    const response = await screeningApi.listTasks({
      keyword: taskHistoryFilters.keyword || undefined,
      status: taskHistoryFilters.status || undefined,
      page: taskHistoryPagination.page,
      pageSize: taskHistoryPagination.pageSize
    })
    taskHistoryRows.value = response.data.items || []
    taskHistoryPagination.total = response.data.total || 0
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '历史初筛任务加载失败，请稍后重试'))
  } finally {
    taskHistoryLoading.value = false
  }
}

const applyTaskProgress = (task) => {
  const recommended = task.recommended_count || 0
  const pending = task.pending_count || 0
  const rejected = task.rejected_count || 0
  Object.assign(progress, {
    status: task.status || 'DRAFT',
    total: task.total_resume_count || 0,
    parsed_success: task.parsed_success_count || 0,
    parsed_failed: task.parsed_failed_count || 0,
    screened: recommended + pending + rejected,
    recommended,
    pending,
    rejected
  })
  currentStage.value = taskStatusText(task.status)
}

const openHistoryTask = async (task) => {
  activeTask.value = task
  applyTaskProgress(task)
  resultRows.value = []
  taskHistoryVisible.value = false
  activeStep.value = 3
  await loadResults()
}

const canContinueHistoryTask = (task) => {
  if (!task || task.status === 'COMPLETED') return false
  const total = task.total_resume_count || 0
  const handled = (task.parsed_success_count || 0) + (task.parsed_failed_count || 0)
  return total > 0 && handled < total
}

const continueHistoryTask = async (task) => {
  activeTask.value = task
  applyTaskProgress(task)
  taskHistoryVisible.value = false
  activeStep.value = 2
  screeningRunning.value = true
  currentStage.value = '继续逐份执行 AI 初筛'
  try {
    await processUploadedResumes(task.id)
    await loadResults()
    activeStep.value = 3
    currentStage.value = '已完成'
    await fetchTaskHistory()
    ElMessage.success('历史任务已继续处理并刷新结果')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, error.message || '继续处理失败，请稍后重试'))
  } finally {
    screeningRunning.value = false
  }
}

const selectPosition = async (position) => {
  selectedPosition.value = position
  try {
    const response = await jobPositionsApi.getById(position.id)
    selectedPosition.value = response.data
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '岗位详情加载失败，请稍后重试'))
  }
}

const isSelectedPosition = (position) => selectedPosition.value?.id === position.id

const openCreatePosition = () => {
  positionDialogMode.value = 'create'
  editingPosition.value = null
  resetPositionForm()
  positionDialogVisible.value = true
}

const openEditPosition = async (position = selectedPosition.value) => {
  if (!position) return
  positionDialogMode.value = 'edit'
  editingPosition.value = position
  resetPositionForm()
  try {
    const response = await jobPositionsApi.getById(position.id)
    editingPosition.value = response.data
    fillPositionForm(response.data)
    positionDialogVisible.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '岗位详情加载失败，请稍后重试'))
  }
}

const parsePositionJd = async () => {
  if (!positionForm.jd_original_text.trim()) {
    ElMessage.warning('请先粘贴岗位 JD 原文')
    return
  }
  aiOverlayVisible.value = true
  aiOverlayTitle.value = 'AI 正在解析岗位 JD'
  aiOverlayStages.value = ['正在读取 JD 原文...', '正在提取岗位信息...', '正在生成筛选规则...', '正在填充表单...']
  aiOverlayProgress.value = 0
  aiOverlayHint.value = '解析完成后可继续修改'
  positionParsing.value = true
  try {
    aiOverlayProgress.value = 20
    const response = await jobPositionsApi.parseJD({ jd_text: positionForm.jd_original_text.trim() })
    aiOverlayProgress.value = 85
    // 渐进填充表单（模块3设计）
    await fillPositionFormAnimated(response.data.position || {})
    aiOverlayProgress.value = 100
    ElMessage.success('岗位信息已生成，可继续修改后保存')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '岗位信息生成失败，请检查 JD 内容后重试'))
  } finally {
    positionParsing.value = false
    aiOverlayVisible.value = false
  }
}

const handlePositionJdFileChange = async (file) => {
  if (!file?.raw) return
  const formData = new FormData()
  formData.append('file', file.raw)
  aiOverlayVisible.value = true
  aiOverlayTitle.value = 'AI 正在解析 JD 文件'
  aiOverlayStages.value = ['正在读取文件...', '正在提取岗位信息...', '正在生成筛选规则...']
  aiOverlayProgress.value = 10
  aiOverlayHint.value = ''
  positionParsing.value = true
  try {
    const response = await screeningApi.parseJdFile(formData)
    aiOverlayProgress.value = 70
    await fillPositionFormAnimated({
      jd_original_text: response.data.jd_text,
      jd_structured_json: response.data.parsed_jd,
      parsed_jd: response.data.parsed_jd
    })
    aiOverlayProgress.value = 100
    ElMessage.success('JD 文件已解析，可继续修改后保存')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, 'JD 文件解析失败，请检查文件后重试'))
  } finally {
    positionParsing.value = false
    setTimeout(() => {
      aiOverlayVisible.value = false
    }, 400)
  }
}

const savePosition = async () => {
  if (!positionForm.position_name.trim()) {
    ElMessage.warning('请填写岗位名称')
    return
  }
  if (!positionForm.jd_original_text.trim()) {
    ElMessage.warning('请先粘贴岗位 JD 原文')
    return
  }

  let saveMode
  if (positionDialogMode.value === 'edit' && (editingPosition.value?.candidate_count || 0) > 0) {
    try {
      await ElMessageBox.confirm(
        '该岗位已产生筛选记录，修改 JD 可能影响历史结果。请选择保存方式。',
        '保存岗位信息',
        {
          confirmButtonText: '保存为新版本',
          cancelButtonText: '仅修改展示信息',
          distinguishCancelAndClose: true,
          type: 'warning'
        }
      )
      saveMode = 'NEW_VERSION'
    } catch (action) {
      if (action === 'cancel') {
        saveMode = 'DISPLAY_ONLY'
      } else {
        return
      }
    }
  }

  positionSaving.value = true
  try {
    const payload = buildPositionPayload(saveMode)
    const response = positionDialogMode.value === 'edit'
      ? await jobPositionsApi.update(editingPosition.value.id, payload)
      : await jobPositionsApi.create(payload)
    selectedPosition.value = response.data
    positionDialogVisible.value = false
    await fetchJobPositions()
    ElMessage.success('岗位已保存到岗位库')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '保存失败，请稍后重试'))
  } finally {
    positionSaving.value = false
  }
}

const archivePosition = async (position) => {
  try {
    await ElMessageBox.confirm(`确认归档「${position.position_name}」？归档后默认不会出现在岗位初筛列表。`, '归档岗位', {
      confirmButtonText: '归档岗位',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await jobPositionsApi.archive(position.id)
    if (selectedPosition.value?.id === position.id) selectedPosition.value = null
    await fetchJobPositions()
    ElMessage.success('岗位已归档')
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      ElMessage.error(getErrorMessage(error, '归档岗位失败，请稍后重试'))
    }
  }
}

const copyPosition = async (position) => {
  try {
    const response = await jobPositionsApi.copy(position.id)
    selectedPosition.value = response.data
    await fetchJobPositions()
    ElMessage.success('岗位已复制')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '复制岗位失败，请稍后重试'))
  }
}

const useSelectedPosition = () => {
  if (!selectedPosition.value) {
    ElMessage.warning('请先选择一个历史岗位')
    return
  }
  activeStep.value = 1
}

const beforeResumeUpload = (file) => {
  const name = file.name.toLowerCase()
  const ok = ['.pdf', '.doc', '.docx'].some((suffix) => name.endsWith(suffix))
  if (!ok) ElMessage.warning('仅支持 PDF / DOC / DOCX 简历文件')
  return ok
}

const handleResumeFileChange = (file, fileList) => {
  const existed = new Map(resumeQueue.value.map((item) => [item.uid, item]))
  resumeUploadList.value = fileList
  resumeQueue.value = fileList.map((item) => {
    const old = existed.get(item.uid)
    if (old) return { ...old, raw: item.raw || old.raw, size: item.size || old.size }
    return {
      uid: item.uid,
      name: item.name,
      size: item.size,
      raw: item.raw,
      status: 'pending',
      parse_status: 'WAITING',
      resume_file_id: null,
      error: ''
    }
  })
}

const handleResumeFileRemove = (file, fileList) => {
  resumeUploadList.value = fileList
  resumeQueue.value = resumeQueue.value.filter((item) => item.uid !== file.uid)
}

const buildJdSnapshot = (position) => ({
  job_position_id: position.id,
  job_position_version: position.version || 1,
  position_name: position.position_name,
  position_type: position.position_type,
  department_name: position.department_name,
  education_requirement: position.education_requirement,
  experience_requirement: position.experience_requirement,
  jd_original_text: position.jd_original_text,
  jd_structured_json: position.jd_structured_json || {},
  screening_rules: normalizeList(position.screening_rules),
  must_have: normalizeList(position.must_have),
  nice_to_have: normalizeList(position.nice_to_have),
  risk_points: normalizeList(position.risk_points),
  interview_questions: normalizeList(position.interview_questions),
  snapshot_source: 'screening_workbench'
})

const resetProgress = () => {
  Object.assign(progress, {
    status: 'DRAFT',
    total: 0,
    parsed_success: 0,
    parsed_failed: 0,
    screened: 0,
    recommended: 0,
    pending: 0,
    rejected: 0
  })
}

const applyUploadedFiles = (files = []) => {
  files.forEach((file, index) => {
    const target = resumeQueue.value.find((item) => item.resume_file_id === file.id)
      || resumeQueue.value.find((item) => item.name === file.file_name)
      || resumeQueue.value[index]
    if (!target) return
    target.resume_file_id = file.id
    target.parse_status = file.parse_status || target.parse_status
    target.error = file.parse_error_message || ''
    target.status = file.parse_status === 'FAILED' ? 'failed' : 'uploaded'
  })
  resumeQueue.value = [...resumeQueue.value]
}

const uploadResumesForTask = async (taskId) => {
  const pendingFiles = resumeQueue.value.filter((item) => item.raw && !item.resume_file_id)
  if (pendingFiles.length === 0) return

  pendingFiles.forEach((item) => {
    item.status = 'uploading'
  })
  const formData = new FormData()
  pendingFiles.forEach((item) => {
    formData.append('files', item.raw, item.name)
  })
  const response = await screeningApi.uploadResumes(taskId, formData)
  applyUploadedFiles(response.data || [])
}

const createScreeningTask = async () => {
  if (activeTask.value) return activeTask.value
  if (!selectedPosition.value) throw new Error('请先选择岗位')

  const payload = {
    task_name: `${selectedPosition.value.position_name} 初筛`,
    job_position_id: selectedPosition.value.id,
    job_position_version: selectedPosition.value.version || 1,
    job_type: selectedPosition.value.position_type,
    jd_structured_json: selectedPosition.value.jd_structured_json || {},
    jd_snapshot_json: buildJdSnapshot(selectedPosition.value)
  }
  const response = await screeningApi.createTask(payload)
  activeTask.value = response.data
  return response.data
}

const processUploadedResumes = async (taskId) => {
  let done = false
  let turns = 0
  const maxTurns = Math.max(resumeQueue.value.length + 5, (progress.total || 0) + 5, 20)
  while (!done) {
    turns += 1
    if (turns > maxTurns) throw new Error('初筛进度异常，请刷新进度后重试')

    const response = await screeningApi.processNextResume(taskId)
    if (response.data.resume_file) applyUploadedFiles([response.data.resume_file])
    if (response.data.progress) Object.assign(progress, response.data.progress)
    const message = response.data.resume_file?.parse_error_message || ''
    currentStage.value = message.includes('复用')
      ? message
      : `正在处理第 ${Math.min(progress.parsed_success + progress.parsed_failed + 1, progress.total || resumeQueue.value.length)} 份简历`
    const handled = (progress.parsed_success || 0) + (progress.parsed_failed || 0)

    // 同步进度到 AI 遮罩
    if (aiOverlayVisible.value) {
      const total = progress.total || resumeQueue.value.length || 1
      const baseProgress = 25
      const maxProgress = 90
      const ratio = handled / total
      aiOverlayProgress.value = Math.min(maxProgress, Math.round(baseProgress + ratio * (maxProgress - baseProgress)))
    }

    done = response.data.done || ((progress.total || 0) > 0 && handled >= progress.total)
  }
}

const startScreening = async () => {
  if (!selectedPosition.value) {
    ElMessage.warning('请先选择一个历史岗位')
    return
  }
  if (resumeQueue.value.length === 0) {
    ElMessage.warning('请先上传简历')
    return
  }

  screeningRunning.value = true
  currentStage.value = '创建初筛任务'
  resetProgress()

  // AI 处理遮罩
  aiOverlayVisible.value = true
  aiOverlayTitle.value = 'AI 正在初筛简历'
  aiOverlayStages.value = [
    '正在创建初筛任务...',
    '正在上传简历文件...',
    '正在逐份解析简历...',
    '正在计算岗位匹配度...',
    '正在生成初筛结论...'
  ]
  aiOverlayProgress.value = 0
  aiOverlayHint.value = '请耐心等待，AI 会逐份处理每份简历'

  try {
    aiOverlayProgress.value = 5
    const task = await createScreeningTask()
    currentStage.value = '上传简历'
    aiOverlayProgress.value = 15
    await uploadResumesForTask(task.id)
    currentStage.value = '逐份执行 AI 初筛'
    aiOverlayProgress.value = 25

    // 处理过程中实时更新遮罩进度
    const originalProcessResumes = processUploadedResumes
    await processUploadedResumes(task.id)

    // 进度由 processUploadedResumes 内部更新 progress reactive，
    // 这里同步到遮罩进度
    currentStage.value = '生成初筛结果'
    aiOverlayProgress.value = 95
    await loadResults()
    activeStep.value = 3
    currentStage.value = '已完成'
    aiOverlayProgress.value = 100
    await fetchJobPositions()
    ElMessage.success('初筛完成，已生成推荐面试名单')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, error.message || '创建初筛任务失败，请稍后重试'))
  } finally {
    screeningRunning.value = false
    // 延迟关闭遮罩让用户看到100%
    setTimeout(() => {
      aiOverlayVisible.value = false
    }, 500)
  }
}

const loadResults = async () => {
  if (!activeTask.value?.id) return
  resultLoading.value = true
  try {
    const response = await screeningApi.getTaskResults(activeTask.value.id, {})
    resultRows.value = response.data.items || []
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '初筛结果加载失败，请稍后重试'))
  } finally {
    resultLoading.value = false
  }
}

const openResultDetail = async (row) => {
  if (!row.result_id) return
  try {
    const response = await screeningApi.getResultDetail(row.result_id)
    selectedDetail.value = response.data
    detailDrawerVisible.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '初筛详情加载失败，请稍后重试'))
  }
}

const changeResultStatus = async (row, status) => {
  if (!row.result_id) return
  try {
    await screeningApi.updateResultStatus(row.result_id, { status })
    await loadResults()
    ElMessage.success('候选人状态已更新')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, '状态更新失败，请稍后重试'))
  }
}

const reprocessResult = async (row, forceParse) => {
  if (!activeTask.value?.id || !row.resume_file_id) return
  row.reprocessing = true
  try {
    const response = await screeningApi.reprocessResume(activeTask.value.id, row.resume_file_id, {
      force_parse: forceParse,
      force_screen: true
    })
    if (response.data.progress) Object.assign(progress, response.data.progress)
    await loadResults()
    ElMessage.success(forceParse ? '已重新解析并完成初筛' : '已基于历史解析重新筛选')
  } catch (error) {
    ElMessage.error(getErrorMessage(error, forceParse ? '重新解析失败，请稍后重试' : '重新筛选失败，请稍后重试'))
  } finally {
    row.reprocessing = false
  }
}

const resetWorkbench = () => {
  activeStep.value = 0
  selectedPosition.value = null
  activeTask.value = null
  resumeUploadList.value = []
  resumeQueue.value = []
  resultRows.value = []
  currentStage.value = '待开始'
  resetProgress()
  fetchJobPositions()
}

const formatFileSize = (size) => {
  if (!size) return '-'
  if (size < 1024 * 1024) return `${Math.round(size / 1024)} KB`
  return `${(size / 1024 / 1024).toFixed(1)} MB`
}

const formatRelativeTime = (value) => {
  if (!value) return '未使用'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '未使用'
  const diff = Date.now() - date.getTime()
  const day = 24 * 60 * 60 * 1000
  if (diff < day && date.getDate() === new Date().getDate()) return '今天'
  if (diff < day * 2) return '昨天'
  return date.toLocaleDateString('zh-CN')
}

const formatDateTime = (value) => {
  if (!value) return '-'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '-'
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const taskStatusText = (status) => ({
  DRAFT: '草稿',
  READY: '待初筛',
  SCREENING: '初筛中',
  COMPLETED: '已完成',
  FAILED: '处理失败'
}[status] || status || '-')

const taskStatusType = (status) => ({
  DRAFT: 'info',
  READY: 'primary',
  SCREENING: 'warning',
  COMPLETED: 'success',
  FAILED: 'danger'
}[status] || 'info')

const uploadStatusText = (status) => ({
  pending: '待上传',
  uploading: '上传中',
  uploaded: '已上传',
  failed: '上传失败'
}[status] || '待上传')

const uploadStatusType = (status) => ({
  pending: 'info',
  uploading: 'warning',
  uploaded: 'success',
  failed: 'danger'
}[status] || 'info')

const parseStatusText = (status) => ({
  WAITING: '待解析',
  UPLOADED: '待解析',
  PARSING: '解析中',
  SCREENING: '初筛中',
  COMPLETED: '已完成',
  FAILED: '解析失败'
}[status] || '待解析')

const parseStatusType = (status) => ({
  WAITING: 'info',
  UPLOADED: 'info',
  PARSING: 'warning',
  SCREENING: 'warning',
  COMPLETED: 'success',
  FAILED: 'danger'
}[status] || 'info')

const resultSourceText = (source) => ({
  AI: 'AI 新生成',
  REUSED: '历史复用'
}[source] || 'AI 新生成')

const resultSourceType = (source) => ({
  AI: 'primary',
  REUSED: 'success'
}[source] || 'primary')

onMounted(() => {
  fetchJobPositions()
})
</script>

<style scoped>
.screening-workbench {
  max-width: 1200px;
  margin: 0 auto;
  color: var(--color-text);
}

.workbench-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 18px;
}

.hero-eyebrow {
  margin: 0 0 6px;
  font-size: 13px;
  font-weight: var(--font-bold);
  color: var(--color-primary);
}

.workbench-hero h1 {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
  letter-spacing: 0;
}

.hero-subtitle {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 14px;
}

.hero-actions {
  flex-shrink: 0;
}

.steps-panel,
.panel {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-lg);
}

.steps-panel {
  padding: 22px 24px;
  margin-bottom: 20px;
}

.setup-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 430px;
  gap: 20px;
  align-items: start;
}

.panel {
  padding: 24px;
}

.panel-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.panel-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: var(--font-bold);
  letter-spacing: 0;
}

.panel-header p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.filter-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 150px auto;
  gap: 10px;
  margin-bottom: 14px;
}

.load-alert {
  margin-bottom: 12px;
}

.position-list {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.position-card {
  min-height: 118px;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
  cursor: pointer;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease, box-shadow 0.18s ease;
}

.position-card:hover {
  border-color: var(--color-primary);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.position-card.selected {
  border-color: var(--color-primary);
  background: var(--color-green-soft);
}

.position-card-main {
  flex: 1;
  min-width: 0;
}

.position-title-line {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.position-title-line h3 {
  margin: 0;
  font-size: 16px;
  font-weight: var(--font-bold);
  letter-spacing: 0;
}

.position-meta {
  margin: 0;
  color: var(--color-gray-700);
  font-size: 13px;
}

.position-foot {
  display: flex;
  gap: 16px;
  margin-top: 18px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.card-more {
  width: 32px;
  height: 32px;
}

.position-empty {
  min-height: 500px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: var(--color-text-secondary);
}

.position-empty .el-icon {
  width: 56px;
  height: 56px;
  margin-bottom: 14px;
  color: var(--color-primary);
  background: var(--color-green-soft);
  border-radius: var(--radius-lg);
}

.position-empty h3 {
  margin: 0 0 8px;
  color: var(--color-text);
  font-size: 17px;
}

.position-empty p {
  max-width: 280px;
  margin: 0;
  line-height: 1.6;
}

.summary-content {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.summary-title {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--color-border);
}

.summary-title h3 {
  margin: 0;
  font-size: 20px;
  font-weight: var(--font-bold);
  letter-spacing: 0;
}

.summary-title p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
}

.summary-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.summary-fields div,
.task-summary-grid div,
.result-stats div {
  padding: 14px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
}

.summary-fields span,
.task-summary-grid span,
.result-stats span {
  display: block;
  color: var(--color-text-secondary);
  font-size: 12px;
  margin-bottom: 6px;
}

.summary-fields strong,
.task-summary-grid strong,
.result-stats strong {
  font-size: 16px;
}

.summary-section {
  padding-top: 2px;
}

.summary-section h4,
.detail-section h4 {
  margin: 0 0 10px;
  font-size: 14px;
  font-weight: var(--font-bold);
}

.summary-section ol,
.detail-section ul {
  margin: 0;
  padding-left: 20px;
  color: var(--color-gray-700);
  line-height: 1.7;
  font-size: 13px;
}

.summary-section.risk li {
  color: #b45309;
}

.muted {
  color: var(--color-text-muted);
  font-size: 13px;
}

.summary-actions,
.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding-top: 8px;
}

.upload-panel,
.confirm-panel,
.result-panel {
  margin-top: 0;
}

.resume-uploader {
  margin-bottom: 20px;
}

.resume-uploader :deep(.el-upload-dragger) {
  padding: 34px 24px;
  border-radius: var(--radius-lg);
  background: var(--color-gray-50);
}

.upload-icon {
  font-size: 46px;
  color: var(--color-primary);
}

.upload-tip {
  color: var(--color-text-secondary);
  font-size: 13px;
  margin-top: 8px;
}

.file-list-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
  margin-bottom: 20px;
}

.file-list-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 16px;
  background: var(--color-gray-50);
  border-bottom: 1px solid var(--color-border);
}

.file-list-title h3 {
  margin: 0;
  font-size: 15px;
}

.file-list-title span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.task-summary-grid,
.result-stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 22px;
}

.screening-flow {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 22px;
}

.result-stats {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}

.result-stats strong {
  font-size: 24px;
}

.candidate-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.candidate-cell span {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.tag-line {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.task-history {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.history-filters {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 140px auto;
  gap: 10px;
}

.history-task-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.history-task-cell strong {
  font-size: 14px;
}

.history-task-cell span,
.history-result-text {
  color: var(--color-text-secondary);
  font-size: 12px;
}

.history-pagination {
  display: flex;
  justify-content: flex-end;
}

.detail-drawer h3 {
  margin: 0 0 18px;
  font-size: 22px;
  letter-spacing: 0;
}

.detail-score {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  padding: 18px;
  margin-bottom: 18px;
  border-radius: var(--radius-md);
  background: var(--color-primary-50);
}

.detail-score span {
  color: var(--color-primary);
}

.detail-score strong {
  color: var(--color-primary);
  font-size: 34px;
}

.detail-section {
  margin-top: 20px;
}

.position-dialog-body {
  display: grid;
  grid-template-columns: 360px minmax(0, 1fr);
  gap: 20px;
  max-height: 68vh;
  overflow: hidden;
}

.jd-input-panel,
.position-form-panel {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 18px;
  background: var(--color-surface);
}

.jd-input-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.jd-input-panel h3,
.position-form-panel h3 {
  margin: 0;
  font-size: 16px;
}

.position-form-panel {
  overflow-y: auto;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0 14px;
}

@media (max-width: 1080px) {
  .setup-grid,
  .position-dialog-body {
    grid-template-columns: 1fr;
  }

  .summary-panel {
    order: -1;
  }

  .screening-flow,
  .task-summary-grid,
  .result-stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .workbench-hero,
  .panel-header,
  .summary-actions,
  .step-actions {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-row,
  .history-filters,
  .summary-fields,
  .screening-flow,
  .task-summary-grid,
  .result-stats,
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
