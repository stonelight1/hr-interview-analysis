<template>
  <div class="candidate-detail" v-if="candidate">
    <div class="detail-header">
      <el-button class="back-button" text @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        {{ backLabel }}
      </el-button>
    </div>

    <section class="page-card decision-hero">
      <div class="hero-person">
        <div class="candidate-title-row">
          <h2 class="candidate-name">{{ candidate.candidate_name }}</h2>
          <el-tag :type="getStatusType(effectiveStatus)" effect="light" size="large">
            {{ getStatusLabel(effectiveStatus) }}
          </el-tag>
        </div>
        <div class="candidate-meta">
          <span class="meta-item"><el-icon :size="14"><OfficeBuilding /></el-icon>{{ candidate.job_name || '岗位 #' + candidate.job_id }}</span>
          <span class="meta-pill" v-if="candidate.job_type">{{ candidate.job_type }}</span>
          <span class="meta-item" v-if="candidate.phone"><el-icon :size="14"><Phone /></el-icon>{{ candidate.phone }}</span>
          <span class="meta-item" v-if="candidate.email"><el-icon :size="14"><Message /></el-icon>{{ candidate.email }}</span>
          <span class="meta-item" v-if="candidate.source"><el-icon :size="14"><Connection /></el-icon>{{ candidate.source }}</span>
        </div>
      </div>

      <div class="hero-advice">
        <div class="score-block">
          <span class="score-number" :style="{ color: getScoreColor(candidate.resume_match_score) }">{{ candidate.resume_match_score ?? '—' }}</span>
          <span class="score-label">简历匹配度</span>
        </div>
        <div class="advice-copy">
          <div class="advice-line"><span>AI 建议：</span>{{ aiAdviceLabel }}</div>
          <div class="advice-line"><span>风险等级：</span><el-tag :type="getRiskType(riskLevel)" effect="light">{{ riskLevel || '—' }}</el-tag></div>
          <p class="advice-summary">{{ decisionConclusion }}</p>
          <p class="ai-disclaimer" v-if="isAiCaution">AI 仅提供筛选建议，最终由 HR 决定。</p>
        </div>
      </div>

      <div class="hero-actions">
        <el-button class="pill-button primary" :loading="screeningLoading && actionState === 'resumePending'" @click="handlePrimaryAction">
          {{ primaryActionText }}
        </el-button>
        <el-button v-if="secondaryActionText" class="pill-button secondary" @click="handleSecondaryAction">
          {{ secondaryActionText }}
        </el-button>
        <el-button v-if="dangerActionText" class="pill-button danger" @click="handleDangerAction">
          {{ dangerActionText }}
        </el-button>
      </div>
    </section>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <el-tab-pane label="决策概览" name="overview">
        <div class="overview-layout">
          <div class="overview-main">
            <section class="page-card content-card">
              <div class="section-header">
                <div>
                  <h3 class="section-title">筛选建议</h3>
                  <p class="section-desc">用于辅助 HR 判断是否推进面试，不作为最终判决。</p>
                </div>
              </div>
              <div class="decision-summary-grid">
                <div class="summary-score">
                  <strong :style="{ color: getScoreColor(candidate.resume_match_score) }">{{ candidate.resume_match_score ?? '—' }}</strong>
                  <span>匹配度</span>
                </div>
                <div class="summary-copy">
                  <div><span>建议：</span>{{ aiAdviceLabel }}</div>
                  <div><span>主要原因：</span>{{ mainReason }}</div>
                  <div class="risk-tags">
                    <span>风险点：</span>
                    <el-tag v-for="item in overviewRisks" :key="item" :type="getRiskType(riskLevel)" effect="light">{{ item }}</el-tag>
                  </div>
                </div>
              </div>
            </section>

            <section class="page-card content-card">
              <div class="section-header">
                <h3 class="section-title">匹配优势</h3>
              </div>
              <div class="brief-list">
                <div v-for="item in overviewStrengths" :key="item.title" class="brief-item success">
                  <strong>{{ item.title }}</strong>
                  <p v-if="item.detail">{{ item.detail }}</p>
                </div>
              </div>
            </section>

          </div>

          <aside class="page-card next-step-card">
            <h3 class="section-title">下一步操作</h3>
            <div class="next-meta">
              <div><span>当前状态</span>{{ getStatusLabel(effectiveStatus) }}</div>
              <div><span>推荐动作</span>{{ recommendedActionText }}</div>
              <div><span>AI 提示</span>{{ decisionConclusion }}</div>
              <div v-if="currentRound"><span>当前轮次</span>{{ currentRound.round_name }}</div>
            </div>
            <el-button class="report-link" text @click="activeTab = 'report'">查看完整简历报告</el-button>
          </aside>
        </div>
      </el-tab-pane>

      <el-tab-pane label="面试问题" name="questions">
        <section class="page-card content-card questions-tab-card">
          <div class="section-header question-header">
            <div>
              <h3 class="section-title">面试问题</h3>
              <p class="section-desc">系统根据当前面试轮次自动判断问题类型，每次生成都会保留历史版本。</p>
            </div>
            <div class="question-actions">
              <div class="current-round-type-hint">
                <span class="hint-label">当前生成</span>
                <span class="hint-value">{{ currentQuestionTypeLabel }}</span>
              </div>
              <el-button
                class="question-generate-button"
                type="primary"
                :loading="questionGenerateLoading"
                :disabled="!canGenerateQuestions"
                @click="generateInterviewQuestions"
              >
                {{ selectedRoundReports.length ? `重新${currentQuestionTypeLabel}` : `生成${currentQuestionTypeLabel}` }}
              </el-button>
            </div>
          </div>

          <el-alert
            v-if="!canGenerateQuestions"
            type="warning"
            show-icon
            :closable="false"
            :title="questionMissingReason"
            class="dialog-alert"
          />

          <div class="question-source-grid">
            <div>
              <span>岗位</span>
              <strong>{{ candidate.job_name || '未绑定岗位' }}</strong>
            </div>
            <div>
              <span>简历</span>
              <strong>{{ candidate.resume_text ? '已导入' : '未上传' }}</strong>
            </div>
            <div>
              <span>初筛报告</span>
              <strong>{{ resumeScreeningReport ? '已生成' : '可选' }}</strong>
            </div>
            <div>
              <span>当前轮次</span>
              <strong>{{ currentRoundNoLabel }}</strong>
            </div>
            <div>
              <span>问题类型</span>
              <strong>{{ currentQuestionTypeLabel }}</strong>
            </div>
            <div>
              <span>最新版本</span>
              <strong>{{ selectedLatestQuestionReport ? `v${selectedLatestQuestionReport.report_version}` : '未生成' }}</strong>
            </div>
          </div>

          <div class="question-workspace">
            <div class="question-main-panel">
              <div class="question-history-select-row">
                <span>历史问题</span>
                <el-select
                  :model-value="selectedQuestionReportId"
                  size="small"
                  placeholder="暂无历史问题"
                  :disabled="interviewQuestionsLoading || !displayedQuestionHistory.length"
                  @change="selectQuestionReportById"
                >
                  <el-option
                    v-for="item in displayedQuestionHistory"
                    :key="item.id"
                    :label="getQuestionHistoryOptionLabel(item)"
                    :value="item.id"
                  />
                </el-select>
                <el-button
                  v-if="otherRoundQuestionHistory.length"
                  text
                  size="small"
                  @click="showAllQuestionHistory = !showAllQuestionHistory"
                >
                  {{ showAllQuestionHistory ? '仅当前轮次' : `全部历史（${otherRoundQuestionHistory.length}）` }}
                </el-button>
              </div>

              <div class="subsection-header">
                <div>
                  <h4>{{ interviewQuestionsReport ? `${interviewQuestionsReport.round_type_label || currentQuestionTypeLabel} v${interviewQuestionsReport.report_version}` : currentQuestionTypeLabel }}</h4>
                  <p>{{ interviewQuestionsReport ? `生成时间：${formatTime(interviewQuestionsReport.created_at)}` : '系统根据当前面试轮次自动判断问题类型。' }}</p>
                </div>
                <el-tag v-if="viewingHistoryReport" type="warning" effect="light">历史版本</el-tag>
              </div>

              <div class="empty-panel" v-if="interviewQuestionsLoading">
                <QuestionPlaceholder :count="5" />
              </div>
              <div class="empty-panel" v-else-if="!generatedQuestions.length">
                <h3>当前暂无{{ currentQuestionTypeLabel }}</h3>
                <p v-if="currentQuestionType === 'FIRST_INTERVIEW'">点击右上角「生成{{ currentQuestionTypeLabel }}」后，系统会基于岗位 JD、候选人简历和初筛报告生成建议问题。</p>
                <p v-else>点击右上角「生成{{ currentQuestionTypeLabel }}」后，系统会结合上一轮面试结果继续生成追问问题。</p>
              </div>
              <div v-else class="generated-question-list">
                <article v-for="(item, index) in generatedQuestions" :key="`${item.question}-${index}`" class="generated-question-card">
                  <div class="question-index">{{ index + 1 }}</div>
                  <div class="question-content">
                    <div class="question-title-row">
                      <h4>{{ item.question }}</h4>
                      <el-tag :type="item.required ? 'danger' : 'info'" effect="light">
                        {{ item.required ? '必问' : '备选' }}
                      </el-tag>
                    </div>
                    <p v-if="item.purpose">{{ item.purpose }}</p>
                    <div class="question-meta">
                      <span v-if="item.dimension">维度：{{ item.dimension }}</span>
                      <span v-if="item.source">依据：{{ item.source }}</span>
                      <span v-if="item.reference">判断：{{ item.reference }}</span>
                    </div>
                  </div>
                </article>
              </div>
            </div>

            <aside class="question-side-panel">
              <section>
                <div class="subsection-header compact">
                  <div>
                    <h4>高频问题 Top 10</h4>
                    <p>当前岗位下{{ currentQuestionTypeLabel }} Top 10。</p>
                  </div>
                </div>
                <div class="empty-stats" v-if="questionStatsLoading">统计中...</div>
                <div class="empty-stats" v-else-if="!questionStats.length">暂无高频问题</div>
                <div v-else class="question-stats-list">
                  <div v-for="(item, index) in questionStats" :key="`${item.question}-${index}`" class="question-stat-item">
                    <div class="stat-rank">{{ index + 1 }}</div>
                    <div>
                      <strong>{{ item.question }}</strong>
                      <p>{{ item.count }} 次｜{{ item.round_type_label || getQuestionRoundLabel(item.round_type) }}<span v-if="item.dimension">｜{{ item.dimension }}</span></p>
                    </div>
                  </div>
                </div>
              </section>
            </aside>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="面试流程" name="interview">
        <section v-if="activeRounds.length === 0" class="page-card empty-interview-card">
          <h3>尚未安排面试</h3>
          <p>安排后将展示本轮必问问题、面试记录和评估结论。</p>
        </section>

        <div v-else class="interview-flow">
          <section class="page-card content-card round-current-card" v-if="currentRound">
            <div class="round-current-head">
              <div>
                <span class="eyebrow">当前轮次</span>
                <h3>{{ currentRound.round_name }}</h3>
                <p>{{ getRoundTimelineDescription(currentRound) || '等待 HR 完善本轮安排。' }}</p>
              </div>
              <el-tag :type="currentRound.status === 'COMPLETED' ? 'success' : 'primary'" effect="light">
                {{ getRoundStatusLabel(currentRound.status) }}
              </el-tag>
            </div>
            <div class="round-meta-grid">
              <div><span>面试时间</span>{{ formatTime(currentRound.scheduled_time) || '—' }}</div>
              <div><span>面试官</span>{{ currentRound.interviewer || '—' }}</div>
              <div><span>本轮关注点</span>{{ currentRound.round_focus || '—' }}</div>
            </div>
          </section>

          <section v-for="round in activeRounds" :key="round.id" class="page-card content-card round-card">
            <div class="round-card-head">
              <div>
                <h3>{{ round.round_name }}</h3>
                <p>{{ round.round_type || '面试' }} / {{ round.round_focus || '未设置关注点' }}</p>
              </div>
              <el-tag :type="round.status === 'COMPLETED' ? 'success' : 'primary'" effect="light">
                {{ getRoundStatusLabel(round.status) }}
              </el-tag>
            </div>

            <div class="round-record" v-if="round.record_text">
              <h4>本轮记录</h4>
              <p>{{ round.record_text }}</p>
            </div>

            <div class="evaluation-grid" v-if="round.status === 'COMPLETED'">
              <div><span>评分</span><strong :style="{ color: getScoreColor(round.score) }">{{ round.score ?? '—' }}</strong></div>
              <div><span>本轮评估</span><strong>{{ round.conclusion || '待填写' }}</strong></div>
              <div><span>HR 决策</span><strong>{{ round.decision || '待决策' }}</strong></div>
            </div>
          </section>
        </div>
      </el-tab-pane>

      <el-tab-pane label="简历报告" name="report">
        <section class="page-card content-card report-tab-card">
          <template v-if="resumeScreeningReport">
            <div class="report-header">
              <div class="report-score-big" :style="{ color: getScoreColor(resumeScreeningReport.score) }">
                {{ resumeScreeningReport.score }}
                <span class="score-unit">分</span>
              </div>
              <div class="report-meta">
                <div><span class="meta-lbl">AI 建议：</span>{{ aiAdviceLabel }}</div>
                <div><span class="meta-lbl">风险等级：</span>{{ resumeScreeningReport.risk_level || riskLevel || '—' }}</div>
                <div><span class="meta-lbl">生成时间：</span>{{ formatTime(resumeScreeningReport.created_at) }}</div>
              </div>
            </div>

            <el-collapse v-model="reportActivePanels" class="report-collapse">
              <el-collapse-item title="筛选结论" name="conclusion">
                <p class="collapse-text">{{ reportSummary }}</p>
              </el-collapse-item>
              <el-collapse-item title="匹配优势" name="strengths">
                <div class="brief-list">
                  <div v-for="item in reportStrengths" :key="item.title" class="brief-item success">
                    <strong>{{ item.title }}</strong>
                    <p v-if="item.detail">{{ item.detail }}</p>
                  </div>
                </div>
              </el-collapse-item>
              <el-collapse-item title="风险与疑点" name="risks">
                <div class="brief-list">
                  <div v-for="item in reportRisks" :key="item.title" class="brief-item danger-soft">
                    <strong>{{ item.title }}</strong>
                    <p v-if="item.detail">{{ item.detail }}</p>
                  </div>
                </div>
              </el-collapse-item>
              <el-collapse-item title="简历原文" name="resume">
                <div class="resume-text">{{ candidate.resume_text }}</div>
              </el-collapse-item>
            </el-collapse>
          </template>
          <div class="empty-panel" v-else>
            <h3>暂无简历筛选报告</h3>
            <p>生成报告后，这里会按结论、风险、问题和简历原文折叠展示。</p>
            <el-button class="pill-button primary" :loading="screeningLoading" @click="triggerResumeScreening">开始简历筛选</el-button>
          </div>
        </section>
      </el-tab-pane>

      <el-tab-pane label="操作记录" name="logs">
        <section class="page-card content-card logs-card">
          <div class="section-header">
            <div>
              <h3 class="section-title">操作记录</h3>
              <p class="section-desc">默认展示最近 5 条流程节点。</p>
            </div>
            <el-button v-if="timelineItems.length > 5" text @click="showAllTimeline = !showAllTimeline">
              {{ showAllTimeline ? '收起' : '查看全部' }}
            </el-button>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="item in visibleTimelineItems"
              :key="item.id"
              :timestamp="item.time"
              :type="item.type"
              placement="top"
            >
              <div class="timeline-item">
                <div class="timeline-title">{{ item.title }}</div>
                <div class="timeline-desc" v-if="item.description">{{ item.description }}</div>
              </div>
            </el-timeline-item>
          </el-timeline>
        </section>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="scheduleDialogVisible" :title="scheduleDialogTitle" width="680px" destroy-on-close>
      <el-alert
        v-if="scheduleForm.round_no > 4"
        type="warning"
        show-icon
        :closable="false"
        title="当前轮次已超过常规建议上限，请确认是否确有必要继续增加面试轮次。"
        class="dialog-alert"
      />
      <el-form label-position="top">
        <el-form-item label="面试轮次">
          <el-input :model-value="`第 ${scheduleForm.round_no} 轮`" disabled />
        </el-form-item>
        <el-form-item label="面试名称">
          <el-input v-model="scheduleForm.round_name" placeholder="例如：第 1 轮面试" />
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="面试类型">
              <el-select v-model="scheduleForm.round_type" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in roundTypeOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="本轮关注点">
              <el-select v-model="scheduleForm.round_focus" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in roundFocusOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="面试方式">
              <el-select v-model="scheduleForm.interview_method" placeholder="请选择" style="width: 100%">
                <el-option v-for="item in interviewMethodOptions" :key="item" :label="item" :value="item" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="面试时间">
              <el-date-picker
                v-model="scheduleForm.scheduled_time"
                type="datetime"
                placeholder="可选"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="面试官">
          <el-input v-model="scheduleForm.interviewer" placeholder="可选" />
        </el-form-item>

      </el-form>
      <template #footer>
        <el-button @click="scheduleDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveScheduledRound">
          {{ scheduleDialogMode === 'edit' ? '保存修改' : '确认安排' }}
        </el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="recordDialogVisible" width="820px" class="record-dialog" destroy-on-close>
      <template #header>
        <div class="record-dialog-header">
          <h2>{{ recordDialogTitle }}</h2>
          <p>将本轮面试内容粘贴或上传，系统会自动分析候选人表现并生成评估建议。</p>
        </div>
      </template>

      <div class="record-dialog-body">
        <div class="record-context-strip">
          <div><span>候选人</span><strong>{{ candidate.candidate_name || '—' }}</strong></div>
          <div><span>岗位</span><strong>{{ candidate.job_name || '岗位 #' + candidate.job_id }}</strong></div>
          <div><span>面试轮次</span><strong>{{ currentRound?.round_name || currentRoundNoLabel }}</strong></div>
          <div><span>本轮关注点</span><strong>{{ currentRound?.round_focus || '待确认' }}</strong></div>
        </div>

        <div class="record-stepper">
          <div class="record-step active"><span>1</span>录入面试对话</div>
          <div class="step-arrow">→</div>
          <div class="record-step"><span>2</span>AI 分析表现</div>
          <div class="step-arrow">→</div>
          <div class="record-step"><span>3</span>生成本轮结论</div>
        </div>

        <el-alert
          v-if="recordGenerating"
          type="info"
          show-icon
          :closable="false"
          title="正在分析本轮面试内容，请稍候..."
          class="dialog-alert"
        />

        <section class="record-input-section">
          <div class="record-section-head">
            <div>
              <h3>面试对话内容</h3>
              <p>请粘贴本轮面试对话、面试纪要或语音转写文本。内容越完整，AI 评估越准确。</p>
            </div>
            <div class="record-upload-area">
              <el-button class="upload-placeholder-button" @click="showUploadUnavailable">
                上传面试文本文件
              </el-button>
              <span>支持 txt / doc / docx / pdf</span>
            </div>
          </div>

          <el-input
            v-model="recordForm.record_text"
            type="textarea"
            :rows="11"
            resize="vertical"
            class="record-textarea"
            placeholder="示例：
面试官：请介绍一下你之前的销售经验。
候选人：我之前主要负责美的净水器线下渠道销售……
面试官：你如何处理客户异议？
候选人：……

也可以粘贴语音转写后的完整文本。"
          />
        </section>

        <el-collapse v-model="recordOptionalPanels" class="record-optional-collapse">
          <el-collapse-item name="manual">
            <template #title>
              <div class="manual-collapse-title">
                <strong>人工补充信息（可选）</strong>
                <span>如 HR 已有明确判断，可在此补充；未填写时系统将根据面试内容自动生成。</span>
              </div>
            </template>
            <el-form label-position="top" class="manual-info-form">
              <el-row :gutter="16">
                <el-col :span="8">
                  <el-form-item label="人工评分">
                    <el-input-number v-model="recordForm.score" :min="0" :max="100" style="width: 100%" />
                  </el-form-item>
                </el-col>
                <el-col :span="16">
                  <el-form-item label="人工结论">
                    <el-input v-model="recordForm.conclusion" placeholder="例如：能力基本匹配，需补充确认稳定性" />
                  </el-form-item>
                </el-col>
              </el-row>
              <el-form-item label="备注">
                <el-input
                  v-model="recordForm.remark"
                  type="textarea"
                  :rows="3"
                  placeholder="可补充薪资、稳定性、到岗时间等 HR 观察。备注当前仅保存在本地草稿。"
                />
              </el-form-item>
            </el-form>
          </el-collapse-item>
        </el-collapse>
      </div>
      <template #footer>
        <div class="record-dialog-footer">
          <el-button @click="recordDialogVisible = false">取消</el-button>
          <div class="record-footer-actions">
            <el-button :disabled="recordGenerating" @click="saveInterviewDraft">保存草稿</el-button>
            <el-button type="primary" class="generate-record-button" :loading="recordGenerating" @click="generateInterviewEvaluation">
              生成本轮评估
            </el-button>
          </div>
        </div>
      </template>
    </el-dialog>

    <AiProcessingOverlay
      :visible="aiOverlayVisible"
      :title="aiOverlayTitle"
      :stages="aiOverlayStages"
      :progress="aiOverlayProgress"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Phone, Message, Connection, OfficeBuilding } from '@element-plus/icons-vue'
import {
  candidatesApi,
  screeningApi,
  interviewRoundsApi,
  interviewQuestionsApi
} from '../api/analysis.js'
import AiProcessingOverlay from '../components/AiProcessingOverlay.vue'
import QuestionPlaceholder from '../components/QuestionPlaceholder.vue'

const route = useRoute()
const router = useRouter()

const candidate = ref(null)
const resumeScreeningReport = ref(null)
const questionHistory = ref([])
const viewingQuestionReport = ref(null)
const showAllQuestionHistory = ref(false)
const hasAppliedLatestQuestionDefault = ref(false)
const questionStats = ref([])
const screeningLoading = ref(false)
const interviewQuestionsLoading = ref(false)
const questionStatsLoading = ref(false)
const questionGenerateLoading = ref(false)

const aiOverlayVisible = ref(false)
const aiOverlayTitle = ref('')
const aiOverlayStages = ref([])
const aiOverlayProgress = ref(0)
const interviewRounds = ref([])
const activeTab = ref('overview')
const reportActivePanels = ref(['conclusion', 'risks'])
const showAllTimeline = ref(false)
const validDetailTabs = new Set(['overview', 'questions', 'interview', 'report', 'logs'])
const backLabel = computed(() => route.query.from === 'interviews' ? '返回面试管理' : '返回候选人库')
const flowState = computed(() => ({
  current_status: candidate.value?.current_status || '',
  current_round_no: candidate.value?.current_round_no ?? null,
  final_conclusion: candidate.value?.final_conclusion || '',
  updated_at: candidate.value?.updated_at || ''
}))

const scheduleDialogVisible = ref(false)
const scheduleDialogMode = ref('schedule')
const editingRoundId = ref(null)
const decisionRoundId = ref(null)
const recordDialogVisible = ref(false)
const recordGenerating = ref(false)
const recordOptionalPanels = ref([])

const roundTypeOptions = ['初面', '复面', '主管面', '终面', '自定义']
const roundFocusOptions = ['基础确认', '能力复核', '风险确认', '薪资沟通', '主管确认', '其他']
const interviewMethodOptions = ['电话', '线上', '线下']
const questionRoundTypeLabels = {
  FIRST_INTERVIEW: '初试问题',
  SECOND_INTERVIEW: '复试问题',
  FINAL_INTERVIEW: '终面问题',
  HR_INTERVIEW: 'HR 面问题',
  OTHER: '其他问题'
}

const scheduleForm = reactive({
  round_no: 1,
  round_name: '第 1 轮面试',
  round_type: '初面',
  round_focus: '基础确认',
  interview_method: '线上',
  scheduled_time: null,
  interviewer: '',
  generate_questions: false,
  based_on_previous: true
})

const recordForm = reactive({
  record_text: '',
  score: null,
  conclusion: '',
  remark: ''
})

const sortedRounds = computed(() => {
  return [...interviewRounds.value].sort((a, b) => {
    if (a.round_no !== b.round_no) return a.round_no - b.round_no
    return String(a.created_at || '').localeCompare(String(b.created_at || ''))
  })
})

const activeRounds = computed(() => sortedRounds.value.filter(round => round.status !== 'CANCELED'))
const scheduledRound = computed(() => activeRounds.value.find(round => round.status === 'SCHEDULED'))
const decisionPendingRound = computed(() => activeRounds.value.find(round => round.status === 'COMPLETED' && !round.decision))
const lastActiveRound = computed(() => activeRounds.value[activeRounds.value.length - 1] || null)
const currentRound = computed(() => scheduledRound.value || decisionPendingRound.value || lastActiveRound.value)
const recordRound = computed(() => currentRound.value || [...sortedRounds.value].reverse().find(round => round.record_text) || null)
const recordDraftKey = computed(() => {
  if (!route.params.id || !currentRound.value?.id) return ''
  return `candidate:${route.params.id}:interview-round:${currentRound.value.id}:record-draft`
})

const maxRoundNo = computed(() => {
  if (!sortedRounds.value.length) return 0
  return Math.max(...sortedRounds.value.map(round => Number(round.round_no) || 0))
})

const nextRoundNo = computed(() => {
  return Math.max(1, maxRoundNo.value + 1)
})

const aiSuggestion = computed(() => resumeScreeningReport.value?.suggestion || candidate.value?.latest_ai_suggestion || '')
const riskLevel = computed(() => resumeScreeningReport.value?.risk_level || getRiskLevelFromSuggestion(aiSuggestion.value))

const parsedReport = computed(() => {
  if (!resumeScreeningReport.value?.report_json) return null
  try {
    return JSON.parse(resumeScreeningReport.value.report_json)
  } catch {
    return null
  }
})

const normalizeReportItem = (item, fallbackTitle = '未命名项') => {
  if (typeof item === 'string') return { title: item, detail: '' }
  if (!item || typeof item !== 'object') return { title: fallbackTitle, detail: '' }
  return {
    title: item.title || item.risk || item.question || item.label || fallbackTitle,
    detail: item.detail || item.evidence || item.purpose || item.reference || ''
  }
}

const reportSummary = computed(() => {
  const report = parsedReport.value
  return report?.summary || report?.overall_comment || normalizeSuggestion(aiSuggestion.value) || '暂无筛选结论。'
})

const reportStrengths = computed(() => {
  const report = parsedReport.value
  const items = report?.strengths || report?.advantages || []
  return items.map(item => normalizeReportItem(item, '匹配优势'))
})

const reportRisks = computed(() => {
  const report = parsedReport.value
  const risks = report?.risk_points || []
  const mismatches = report?.mismatches || report?.weaknesses || []
  return [...risks, ...mismatches].map(item => normalizeReportItem(item, '风险与疑点'))
})

const overviewStrengths = computed(() => {
  const items = reportStrengths.value.slice(0, 3)
  return items.length ? items : [
    { title: '待生成匹配优势', detail: '生成简历筛选报告后展示核心优势。' }
  ]
})

const overviewRisks = computed(() => {
  const items = reportRisks.value.slice(0, 3).map(item => item.title)
  return items.length ? items : ['稳定性', '薪资匹配度', '岗位意愿']
})

const getQuestionRoundLabel = (type) => {
  if (!type) return '未标记轮次'
  return questionRoundTypeLabels[type] || type
}

/**
 * 根据候选人当前面试状态自动判断问题类型。
 * 优先使用 currentRound 的 round_no 和 round_type 字段，
 * 回退到候选人 current_status 硬编码映射。
 */
const currentQuestionType = computed(() => {
  // 优先：基于当前轮次编号判断
  const roundNo = currentRound.value?.round_no ?? candidate.value?.current_round_no
  if (roundNo != null) {
    const no = Number(roundNo)
    // 检查当前轮次的 round_type 是否为 HR 面
    const roundType = currentRound.value?.round_type
    if (roundType === 'HR面' || roundType === 'HR 面' || roundType === 'HR面试') {
      return 'HR_INTERVIEW'
    }
    if (no >= 4) return 'FINAL_INTERVIEW'
    if (no === 3) return 'FINAL_INTERVIEW'
    if (no === 2) return 'SECOND_INTERVIEW'
    return 'FIRST_INTERVIEW'
  }

  // 回退：基于候选人状态映射
  const status = candidate.value?.current_status || ''
  // HR 面相关状态
  if (status.includes('HR')) return 'HR_INTERVIEW'
  // 终面相关状态：初试通过且复试通过
  if (status === 'SECOND_INTERVIEW_PASSED') return 'FINAL_INTERVIEW'
  // 复试相关状态
  if (status.startsWith('SECOND_INTERVIEW')) return 'SECOND_INTERVIEW'
  if (status === 'FIRST_INTERVIEW_PASSED') return 'SECOND_INTERVIEW'
  // 默认：初试
  return 'FIRST_INTERVIEW'
})

const currentQuestionTypeLabel = computed(() => getQuestionRoundLabel(currentQuestionType.value))

const currentRoundNoLabel = computed(() => {
  const roundNo = currentRound.value?.round_no ?? candidate.value?.current_round_no
  if (roundNo != null) return `第 ${roundNo} 轮面试`
  const status = candidate.value?.current_status || ''
  if (status === 'INTERVIEW_WAITING' || status === 'RESUME_PASSED') return '第 1 轮面试'
  return '待安排'
})

const isKnownQuestionRoundType = (type) => {
  return type in questionRoundTypeLabels
}

const latestQuestionReport = computed(() => questionHistory.value[0] || null)

const selectedQuestionReportId = computed(() => interviewQuestionsReport.value?.id || null)

const selectedRoundReports = computed(() => {
  return questionHistory.value.filter(item => item.round_type === currentQuestionType.value)
})

const selectedLatestQuestionReport = computed(() => selectedRoundReports.value[0] || null)

/** 当前轮次的历史问题 */
const currentRoundQuestionHistory = computed(() => {
  return questionHistory.value.filter(item => item.round_type === currentQuestionType.value)
})

/** 其他轮次的历史问题 */
const otherRoundQuestionHistory = computed(() => {
  return questionHistory.value.filter(item => item.round_type !== currentQuestionType.value)
})

/** 下拉框中实际展示的问题列表：默认仅当前轮次，展开后包含全部 */
const displayedQuestionHistory = computed(() => {
  if (showAllQuestionHistory.value) return questionHistory.value
  return currentRoundQuestionHistory.value
})

const viewingHistoryReport = computed(() => {
  return Boolean(viewingQuestionReport.value && viewingQuestionReport.value.id !== latestQuestionReport.value?.id)
})

const interviewQuestionsReport = computed(() => {
  return viewingQuestionReport.value || selectedLatestQuestionReport.value || null
})

const getQuestionHistoryOptionLabel = (report) => {
  const typeLabel = report.round_type_label || getQuestionRoundLabel(report.round_type)
  const version = report.report_version ? `v${report.report_version}` : '未标记版本'
  const count = `${report.question_count || 0}题`
  const time = formatDateOnly(report.created_at)
  return `${typeLabel} ${version}｜${count}｜${time}`
}

const parsedInterviewQuestionsReport = computed(() => {
  if (!interviewQuestionsReport.value?.report_json) return null
  try {
    const data = JSON.parse(interviewQuestionsReport.value.report_json)
    return data && typeof data === 'object' ? data : null
  } catch {
    return null
  }
})

const normalizeQuestionItem = (item) => {
  if (typeof item === 'string') {
    return { question: item, purpose: '', dimension: '', source: '', reference: '', required: true }
  }
  if (!item || typeof item !== 'object') {
    return { question: '未命名面试题', purpose: '', dimension: '', source: '', reference: '', required: false }
  }
  return {
    question: item.question || item.title || item.detail || '未命名面试题',
    purpose: item.purpose || '',
    dimension: item.dimension || item.category || '',
    source: item.source || '',
    reference: item.reference || item.evaluation_reference || '',
    required: item.required !== false
  }
}

const generatedQuestions = computed(() => {
  const responseQuestions = interviewQuestionsReport.value?.questions
  const reportQuestions = parsedInterviewQuestionsReport.value?.questions
  const questions = Array.isArray(responseQuestions) ? responseQuestions : (Array.isArray(reportQuestions) ? reportQuestions : [])
  return questions.map(normalizeQuestionItem)
})

const canGenerateQuestions = computed(() => {
  return Boolean(candidate.value?.job_id && candidate.value?.resume_text?.trim())
})

const questionMissingReason = computed(() => {
  if (!candidate.value?.job_id) return '该候选人尚未绑定岗位，请先选择历史岗位。'
  if (!candidate.value?.resume_text?.trim()) return '该候选人暂无简历，请先上传简历。'
  return ''
})

const mainReason = computed(() => {
  const text = reportSummary.value || ''
  if (!text || text === '暂无筛选结论。') return '有相关经验，但稳定性和薪资期望需复核'
  return text.length > 56 ? `${text.slice(0, 56)}...` : text
})

const decisionConclusion = computed(() => mainReason.value)

const aiAdviceLabel = computed(() => {
  const suggestion = normalizeSuggestion(aiSuggestion.value)
  if (suggestion.includes('淘汰') || suggestion.includes('不建议')) return '谨慎推进'
  if (suggestion.includes('暂') || suggestion.includes('人才库')) return '暂缓推进'
  if (suggestion.includes('约') || suggestion.includes('进入') || suggestion.includes('推荐')) return '建议推进'
  if (resumeScreeningReport.value) return 'HR 复核后决定'
  return '等待筛选'
})

const isAiCaution = computed(() => {
  const suggestion = normalizeSuggestion(aiSuggestion.value)
  return suggestion.includes('淘汰') || suggestion.includes('不建议')
})

const recommendedActionText = computed(() => {
  if (actionState.value === 'readyToArrange') return 'HR 复核后决定是否安排面试'
  if (actionState.value === 'scheduled') return '完成本轮评估'
  if (actionState.value === 'decision') return '决定安排下一轮、结束流程或淘汰'
  if (actionState.value === 'hold') return '重新打开流程后继续推进'
  if (effectiveStatus.value === 'FINAL_PASSED') return '查看最终报告'
  if (effectiveStatus.value === 'REJECTED') return '可恢复候选人或查看报告'
  return '先生成简历筛选报告'
})

const primaryActionText = computed(() => {
  if (actionState.value === 'resumePending') return screeningLoading.value ? '筛选中...' : '生成简历筛选'
  if (actionState.value === 'readyToArrange') return `安排第 ${nextRoundNo.value} 轮面试`
  if (actionState.value === 'scheduled') return '录入面试并评估'
  if (actionState.value === 'decision') return '安排下一轮'
  if (actionState.value === 'hold') return '恢复候选人'
  if (effectiveStatus.value === 'FINAL_PASSED') return '查看最终报告'
  if (effectiveStatus.value === 'REJECTED' || effectiveStatus.value === 'CLOSED') return '恢复候选人'
  return '查看报告'
})

const secondaryActionText = computed(() => {
  if (actionState.value === 'readyToArrange') return '标记待定'
  if (actionState.value === 'scheduled') return '修改面试安排'
  if (actionState.value === 'decision') return '结束流程'
  if (actionState.value === 'hold') return '安排面试'
  if (effectiveStatus.value === 'REJECTED' || effectiveStatus.value === 'CLOSED') return '查看报告'
  return ''
})

const dangerActionText = computed(() => {
  if (actionState.value === 'readyToArrange') return '淘汰'
  if (actionState.value === 'scheduled') return '取消面试'
  if (actionState.value === 'decision') return '淘汰'
  if (actionState.value === 'hold') return '淘汰候选人'
  return ''
})

const effectiveStatus = computed(() => {
  const backendStatus = candidate.value?.current_status || ''
  if (backendStatus === 'INTERVIEW_WAITING') return 'WAITING_TO_SCHEDULE'
  if (['INTERVIEW_SCHEDULED', 'INTERVIEW_DECISION_PENDING', 'FINAL_PASSED', 'REJECTED', 'ON_HOLD'].includes(backendStatus)) return backendStatus
  if (backendStatus === 'RESUME_REJECTED') return 'REJECTED'
  if (backendStatus === 'TALENT_POOL' || backendStatus === 'RESUME_TBD') return 'ON_HOLD'
  if (backendStatus === 'HIRED') return 'FINAL_PASSED'
  if (backendStatus === 'ABANDONED' || backendStatus === 'OFFER_ABANDONED') return 'CLOSED'
  if (['FIRST_INTERVIEW_PENDING', 'SECOND_INTERVIEW_PENDING', 'FIRST_INTERVIEW_IN_PROGRESS', 'SECOND_INTERVIEW_IN_PROGRESS'].includes(backendStatus)) return 'INTERVIEW_SCHEDULED'
  if (['FIRST_INTERVIEW_PASSED', 'SECOND_INTERVIEW_PASSED'].includes(backendStatus)) return 'INTERVIEW_DECISION_PENDING'
  if (['FIRST_INTERVIEW_REJECTED', 'SECOND_INTERVIEW_REJECTED'].includes(backendStatus)) return 'REJECTED'
  if (['RESUME_PASSED', 'RESUME_SCREENING_DONE'].includes(backendStatus)) return 'WAITING_TO_SCHEDULE'
  if (resumeScreeningReport.value) return inferStatusFromScreening(resumeScreeningReport.value)
  if (backendStatus === 'RESUME_PENDING' || backendStatus === 'IMPORTED') return 'RESUME_PENDING'
  return backendStatus || 'RESUME_PENDING'
})

const actionState = computed(() => {
  const status = effectiveStatus.value
  if (['FINAL_PASSED', 'REJECTED', 'CLOSED'].includes(status)) return 'closed'
  if (status === 'ON_HOLD') return 'hold'
  if (decisionPendingRound.value) return 'decision'
  if (scheduledRound.value) return 'scheduled'
  if (status === 'WAITING_TO_SCHEDULE') return 'readyToArrange'
  if (status === 'RESUME_PENDING') return 'resumePending'
  return resumeScreeningReport.value ? 'readyToArrange' : 'resumePending'
})

const decisionAdvice = computed(() => {
  const suggestion = aiSuggestion.value
  if (suggestion.includes('淘汰') || suggestion.includes('不建议')) return '建议淘汰，需 HR 复核'
  if (suggestion.includes('人才库') || suggestion.includes('暂')) return '建议暂定观察'
  if (suggestion.includes('约') || suggestion.includes('进入')) return '建议安排面试'
  if (effectiveStatus.value === 'WAITING_TO_SCHEDULE') return '待安排面试'
  if (effectiveStatus.value === 'INTERVIEW_DECISION_PENDING') return '等待 HR 决策'
  return '等待 HR 判断下一步'
})

const actionHint = computed(() => {
  if (actionState.value === 'readyToArrange') return '简历筛选已完成，由 HR 决定是否安排第 1 轮面试。'
  if (actionState.value === 'scheduled') return '本轮面试已创建，完成后填写面试记录。'
  if (actionState.value === 'decision') return '面试记录已填写，请决定结束、进入下一轮、暂定或淘汰。'
  if (actionState.value === 'closed') return '候选人流程已结束，只保留查看和重新打开入口。'
  if (actionState.value === 'hold') return '候选人已暂定，可重新打开后继续推进。'
  return '请先完成简历筛选，再决定是否安排面试。'
})

const recordHint = computed(() => {
  if (!recordRound.value) return '面试安排创建后可填写记录。'
  if (recordRound.value.status === 'SCHEDULED') return '面试未完成，当前只展示安排信息。'
  return '面试完成后，HR 在当前操作区决定下一步。'
})

const scheduleDialogTitle = computed(() => {
  if (scheduleDialogMode.value === 'edit') return '修改面试安排'
  if (scheduleDialogMode.value === 'next') return '安排下一轮面试'
  return '安排面试'
})

const recordDialogTitle = computed(() => {
  const roundName = currentRound.value?.round_name || currentRoundNoLabel.value || '本轮面试'
  return `上传/录入${roundName}对话`
})

const timelineItems = computed(() => {
  const items = []
  items.push({
    id: 'resume-parsed',
    title: '简历解析完成',
    description: candidate.value?.parsed_resume_json ? '已提取候选人基础信息。' : '已导入简历文本，可用于筛选和面试问题生成。',
    time: formatTime(candidate.value?.created_at),
    type: 'success'
  })

  if (resumeScreeningReport.value || candidate.value?.resume_match_score != null || ['WAITING_TO_SCHEDULE', 'INTERVIEW_SCHEDULED', 'INTERVIEW_DECISION_PENDING', 'FINAL_PASSED', 'REJECTED', 'ON_HOLD'].includes(effectiveStatus.value)) {
    items.push({
      id: 'resume-screened',
      title: `简历筛选完成${aiSuggestion.value ? '，AI ' + normalizeSuggestion(aiSuggestion.value) : ''}`,
      description: candidate.value?.resume_match_score != null ? `简历匹配度 ${candidate.value.resume_match_score} 分。` : '等待 HR 根据筛选结果决策。',
      time: formatTime(resumeScreeningReport.value?.created_at || candidate.value?.updated_at),
      type: getTimelineTypeFromSuggestion(aiSuggestion.value)
    })
  }

  if (activeRounds.value.length === 0 && effectiveStatus.value === 'WAITING_TO_SCHEDULE') {
    items.push({
      id: 'round-1-waiting',
      title: '第 1 轮面试待安排',
      description: 'HR 点击“安排面试”后才会创建第 1 轮面试。',
      time: '',
      type: 'warning'
    })
  }

  sortedRounds.value.forEach(round => {
    if (round.status === 'CANCELED') {
      items.push({
        id: `${round.id}-canceled`,
        title: `${round.round_name}已取消`,
        description: round.round_focus ? `原定重点：${round.round_focus}` : '',
        time: formatTime(round.updated_at),
        type: 'info'
      })
      return
    }

    items.push({
      id: `${round.id}-scheduled`,
      title: `${round.round_name}已安排`,
      description: getRoundTimelineDescription(round),
      time: formatTime(round.scheduled_time || round.created_at),
      type: round.status === 'SCHEDULED' ? 'primary' : 'success'
    })

    if (round.status === 'COMPLETED') {
      items.push({
        id: `${round.id}-completed`,
        title: `${round.round_name}已完成，结论：${round.decision || '待 HR 决策'}`,
        description: round.conclusion || '已填写面试记录。',
        time: formatTime(round.updated_at),
        type: round.decision === '淘汰' ? 'danger' : (round.decision === '暂定' ? 'warning' : 'success')
      })
    }
  })

  if (effectiveStatus.value === 'FINAL_PASSED') {
    items.push({ id: 'final-passed', title: '流程已结束，结论：通过并结束', description: '', time: formatTime(flowState.value.updated_at), type: 'success' })
  } else if (effectiveStatus.value === 'REJECTED') {
    items.push({ id: 'final-rejected', title: '流程已结束，结论：淘汰', description: '', time: formatTime(flowState.value.updated_at), type: 'danger' })
  } else if (effectiveStatus.value === 'ON_HOLD') {
    items.push({ id: 'final-hold', title: '候选人暂定', description: '后续可重新打开流程。', time: formatTime(flowState.value.updated_at), type: 'warning' })
  }

  return items
})

const visibleTimelineItems = computed(() => {
  if (showAllTimeline.value) return timelineItems.value
  return timelineItems.value.slice(-5)
})

const getStatusType = (status) => {
  const map = {
    RESUME_PENDING: 'warning',
    WAITING_TO_SCHEDULE: 'warning',
    INTERVIEW_SCHEDULED: 'primary',
    INTERVIEW_DECISION_PENDING: 'warning',
    ON_HOLD: 'info',
    FINAL_PASSED: 'success',
    REJECTED: 'danger',
    CLOSED: 'info'
  }
  return map[status] || 'info'
}

const getRoundStatusLabel = (status) => {
  const map = {
    SCHEDULED: '待面试',
    COMPLETED: '已完成',
    CANCELED: '已取消'
  }
  return map[status] || status || '—'
}

const getStatusLabel = (status) => {
  const map = {
    IMPORTED: '简历待解析',
    RESUME_PENDING: '简历待筛选',
    WAITING_TO_SCHEDULE: '待安排面试',
    INTERVIEW_SCHEDULED: '面试待进行',
    INTERVIEW_DECISION_PENDING: '面试完成待决策',
    ON_HOLD: '暂定',
    FINAL_PASSED: '通过并结束',
    REJECTED: '已淘汰',
    CLOSED: '已结束'
  }
  return map[status] || status
}

const getScoreColor = (score) => {
  if (score === null || score === undefined || score === '') return '#9CA3AF'
  if (score >= 80) return '#10B981'
  if (score >= 60) return '#F59E0B'
  return '#EF4444'
}

const getSuggestionType = (suggestion) => {
  if (!suggestion) return 'info'
  if (suggestion.includes('淘汰') || suggestion.includes('不建议')) return 'danger'
  if (suggestion.includes('暂') || suggestion.includes('人才库')) return 'warning'
  return 'success'
}

const getRiskType = (level) => {
  if (level === '低') return 'success'
  if (level === '中') return 'warning'
  if (level === '高') return 'danger'
  return 'info'
}

const getRiskLevelFromSuggestion = (suggestion) => {
  if (!suggestion) return ''
  if (suggestion.includes('淘汰') || suggestion.includes('不建议')) return '高'
  if (suggestion.includes('暂') || suggestion.includes('人才库')) return '中'
  return '低'
}

const normalizeSuggestion = (suggestion) => {
  if (!suggestion) return ''
  return String(suggestion)
    .replaceAll('约初试', '约面试')
    .replaceAll('初试', '本轮面试')
    .replaceAll('复试', '下一轮')
}

const formatTime = (time) => {
  if (!time) return ''
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return ''
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const formatDateOnly = (time) => {
  if (!time) return '—'
  const date = new Date(time)
  if (Number.isNaN(date.getTime())) return '—'
  return `${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

const inferStatusFromScreening = (report) => {
  if (!report) return 'RESUME_PENDING'
  return 'WAITING_TO_SCHEDULE'
}

const getTimelineTypeFromSuggestion = (suggestion) => {
  if (!suggestion) return 'success'
  if (suggestion.includes('淘汰') || suggestion.includes('不建议')) return 'danger'
  if (suggestion.includes('暂') || suggestion.includes('人才库')) return 'warning'
  return 'success'
}

const getRoundTimelineDescription = (round) => {
  const parts = []
  if (round.round_type) parts.push(round.round_type)
  if (round.round_focus) parts.push(round.round_focus)
  if (round.interview_method) parts.push(round.interview_method)
  if (round.interviewer) parts.push(`面试官：${round.interviewer}`)
  return parts.join(' / ')
}

const fetchCandidate = async () => {
  try {
    const response = await candidatesApi.getById(route.params.id)
    candidate.value = response.data
  } catch {
    ElMessage.error('获取候选人详情失败')
  }
}

const fetchResumeScreeningReport = async () => {
  try {
    const response = await screeningApi.getLatest(route.params.id)
    resumeScreeningReport.value = response.data
  } catch {
    resumeScreeningReport.value = null
  }
}

const fetchInterviewRounds = async () => {
  try {
    const response = await interviewRoundsApi.list(route.params.id)
    interviewRounds.value = Array.isArray(response.data) ? response.data : []
  } catch {
    interviewRounds.value = []
  }
}

const applyLatestQuestionDefault = () => {
  if (hasAppliedLatestQuestionDefault.value || !questionHistory.value.length) return
  hasAppliedLatestQuestionDefault.value = true
  // 默认选中当前轮次的最新问题版本
  const currentTypeLatest = selectedLatestQuestionReport.value
  if (currentTypeLatest) {
    viewingQuestionReport.value = null
  } else if (isKnownQuestionRoundType(questionHistory.value[0].round_type)) {
    viewingQuestionReport.value = questionHistory.value[0]
  } else {
    viewingQuestionReport.value = questionHistory.value[0]
  }
}

const fetchInterviewQuestions = async () => {
  interviewQuestionsLoading.value = true
  try {
    const response = await interviewQuestionsApi.list(route.params.id, { page: 1, pageSize: 50 })
    questionHistory.value = Array.isArray(response.data?.items) ? response.data.items : []
    applyLatestQuestionDefault()
    if (viewingQuestionReport.value && !questionHistory.value.some(item => item.id === viewingQuestionReport.value.id)) {
      viewingQuestionReport.value = null
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取面试问题失败')
    questionHistory.value = []
  } finally {
    interviewQuestionsLoading.value = false
  }
}

const fetchQuestionStats = async () => {
  if (!candidate.value?.job_id) {
    questionStats.value = []
    return
  }
  questionStatsLoading.value = true
  try {
    const response = await interviewQuestionsApi.stats({
      jobPositionId: candidate.value.job_id,
      roundType: currentQuestionType.value,
      limit: 10
    })
    questionStats.value = Array.isArray(response.data?.items) ? response.data.items : []
  } catch (error) {
    questionStats.value = []
    ElMessage.error(error.response?.data?.detail || '获取高频问题失败')
  } finally {
    questionStatsLoading.value = false
  }
}

const selectQuestionReport = (report) => {
  viewingQuestionReport.value = report
}

const selectQuestionReportById = (reportId) => {
  const report = questionHistory.value.find(item => item.id === reportId)
  if (report) {
    selectQuestionReport(report)
  }
}

const refreshFlow = async () => {
  await Promise.all([fetchCandidate(), fetchInterviewRounds()])
}

const triggerResumeScreening = async () => {
  screeningLoading.value = true
  aiOverlayTitle.value = '正在简历筛选'
  aiOverlayStages.value = ['解析简历内容', '匹配岗位要求', '评估风险点', '生成筛选建议']
  aiOverlayProgress.value = 10
  aiOverlayVisible.value = true

  setTimeout(() => { aiOverlayProgress.value = 30 }, 600)
  setTimeout(() => { aiOverlayProgress.value = 55 }, 1800)
  setTimeout(() => { aiOverlayProgress.value = 80 }, 3500)

  try {
    const response = await screeningApi.trigger(route.params.id, { force: false, request_id: null })
    resumeScreeningReport.value = response.data
    aiOverlayProgress.value = 100
    await refreshFlow()
    setTimeout(() => {
      aiOverlayVisible.value = false
      ElMessage.success('简历筛选完成')
    }, 500)
  } catch (error) {
    aiOverlayVisible.value = false
    ElMessage.error(error.response?.data?.detail || '简历筛选失败')
  } finally {
    screeningLoading.value = false
  }
}

const openScheduleDialog = (mode, round = null) => {
  scheduleDialogMode.value = mode
  editingRoundId.value = round?.id || null
  decisionRoundId.value = mode === 'next' ? decisionPendingRound.value?.id || currentRound.value?.id || null : null

  const roundNo = mode === 'edit' && round ? round.round_no : nextRoundNo.value
  scheduleForm.round_no = roundNo
  scheduleForm.round_name = round?.round_name || `第 ${roundNo} 轮面试`
  scheduleForm.round_type = round?.round_type || (roundNo === 1 ? '初面' : '复面')
  scheduleForm.round_focus = round?.round_focus || (roundNo === 1 ? '基础确认' : '能力复核')
  scheduleForm.interview_method = round?.interview_method || '线上'
  scheduleForm.scheduled_time = round?.scheduled_time || null
  scheduleForm.interviewer = round?.interviewer || ''
  scheduleForm.generate_questions = false
  scheduleForm.based_on_previous = true

  if (roundNo > 4) {
    ElMessage.warning('当前候选人面试轮次已超过常规建议上限，请确认是否需要继续。')
  }
  scheduleDialogVisible.value = true
}

const buildRoundPayload = () => ({
  round_no: scheduleForm.round_no,
  round_name: scheduleForm.round_name,
  round_type: scheduleForm.round_type,
  round_focus: scheduleForm.round_focus,
  interview_method: scheduleForm.interview_method,
  scheduled_time: scheduleForm.scheduled_time,
  interviewer: scheduleForm.interviewer,
  generate_questions: scheduleForm.generate_questions,
  based_on_previous: scheduleForm.based_on_previous
})

const saveScheduledRound = async () => {
  if (!scheduleForm.round_name.trim()) {
    ElMessage.warning('请填写面试名称')
    return
  }

  try {
    if (scheduleDialogMode.value === 'edit') {
      await interviewRoundsApi.update(route.params.id, editingRoundId.value, buildRoundPayload())
    } else if (scheduleDialogMode.value === 'next') {
      await interviewRoundsApi.decide(route.params.id, decisionRoundId.value, {
        decision: '进入下一轮',
        next_round: buildRoundPayload()
      })
    } else {
      await interviewRoundsApi.create(route.params.id, buildRoundPayload())
    }
    await refreshFlow()
    scheduleDialogVisible.value = false
    ElMessage.success(scheduleDialogMode.value === 'edit' ? '面试安排已更新' : '面试已创建')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存面试安排失败')
  }
}

const loadInterviewDraft = () => {
  if (!recordDraftKey.value || typeof window === 'undefined') return null
  try {
    const raw = window.localStorage.getItem(recordDraftKey.value)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

const clearInterviewDraft = () => {
  if (!recordDraftKey.value || typeof window === 'undefined') return
  try {
    window.localStorage.removeItem(recordDraftKey.value)
  } catch {
    // Local draft cleanup is best-effort only.
  }
}

const openRecordDialog = () => {
  if (!currentRound.value) return
  recordForm.record_text = currentRound.value.record_text || ''
  recordForm.score = currentRound.value.score ?? null
  recordForm.conclusion = currentRound.value.conclusion || ''
  recordForm.remark = ''
  recordOptionalPanels.value = []
  recordGenerating.value = false

  const draft = loadInterviewDraft()
  if (draft) {
    recordForm.record_text = draft.record_text || recordForm.record_text
    recordForm.score = draft.score ?? recordForm.score
    recordForm.conclusion = draft.conclusion || recordForm.conclusion
    recordForm.remark = draft.remark || ''
    if (recordForm.score != null || recordForm.conclusion || recordForm.remark) {
      recordOptionalPanels.value = ['manual']
    }
  }
  recordDialogVisible.value = true
}

const saveInterviewDraft = () => {
  if (!currentRound.value) return
  const hasDraftContent = Boolean(
    recordForm.record_text.trim()
    || recordForm.conclusion.trim()
    || recordForm.remark.trim()
    || recordForm.score != null
  )
  if (!hasDraftContent) {
    ElMessage.warning('暂无可保存的面试对话草稿')
    return
  }
  if (!recordDraftKey.value || typeof window === 'undefined') {
    ElMessage.error('当前环境不支持本地草稿保存')
    return
  }
  try {
    window.localStorage.setItem(recordDraftKey.value, JSON.stringify({
      record_text: recordForm.record_text,
      score: recordForm.score,
      conclusion: recordForm.conclusion,
      remark: recordForm.remark,
      updated_at: new Date().toISOString()
    }))
    ElMessage.success('草稿已保存在本地，暂未触发 AI 分析')
  } catch {
    ElMessage.error('保存草稿失败，请检查浏览器本地存储权限')
  }
}

const showUploadUnavailable = () => {
  ElMessage.info('当前仅支持粘贴文本，文件上传功能后续开放')
}

const generateInterviewEvaluation = async () => {
  if (!currentRound.value) return
  if (!recordForm.record_text.trim()) {
    ElMessage.warning('请先粘贴或上传本轮面试对话内容。')
    return
  }
  recordGenerating.value = true
  try {
    await interviewRoundsApi.submitRecord(route.params.id, currentRound.value.id, {
      record_text: recordForm.record_text,
      score: recordForm.score,
      conclusion: recordForm.conclusion
    })
    clearInterviewDraft()
    await refreshFlow()
    recordDialogVisible.value = false
    ElMessage.success('本轮面试内容已保存，评估结果已刷新')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '生成本轮评估失败')
  } finally {
    recordGenerating.value = false
  }
}

const cancelInterview = async () => {
  if (!scheduledRound.value) return
  try {
    await interviewRoundsApi.cancel(route.params.id, scheduledRound.value.id)
    await refreshFlow()
    ElMessage.success('面试已取消')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '取消面试失败')
  }
}

const passAndClose = () => {
  applyDecision('通过并结束')
}

const holdCandidate = () => {
  applyDecision('暂定')
}

const rejectCandidate = () => {
  applyDecision('淘汰')
}

const handlePrimaryAction = () => {
  if (actionState.value === 'resumePending') {
    triggerResumeScreening()
    return
  }
  if (actionState.value === 'readyToArrange') {
    openScheduleDialog('schedule')
    return
  }
  if (actionState.value === 'scheduled') {
    openRecordDialog()
    return
  }
  if (actionState.value === 'decision') {
    openScheduleDialog('next')
    return
  }
  if (actionState.value === 'hold') {
    reopenFlow()
    return
  }
  if (effectiveStatus.value === 'FINAL_PASSED') {
    activeTab.value = 'report'
    return
  }
  if (effectiveStatus.value === 'REJECTED' || effectiveStatus.value === 'CLOSED') {
    reopenFlow()
    return
  }
  activeTab.value = 'report'
}

const handleSecondaryAction = () => {
  if (actionState.value === 'readyToArrange') {
    holdCandidate()
    return
  }
  if (actionState.value === 'scheduled') {
    openScheduleDialog('edit', currentRound.value)
    return
  }
  if (actionState.value === 'decision') {
    passAndClose()
    return
  }
  if (actionState.value === 'hold') {
    openScheduleDialog('schedule')
    return
  }
  activeTab.value = 'report'
}

const handleDangerAction = () => {
  if (actionState.value === 'scheduled') {
    cancelInterview()
    return
  }
  rejectCandidate()
}

const applyDecision = async (decision) => {
  const round = decisionPendingRound.value || currentRound.value
  try {
    if (!round) {
      const statusMap = {
        暂定: 'ON_HOLD',
        淘汰: 'REJECTED',
        通过并结束: 'FINAL_PASSED'
      }
      const toStatus = statusMap[decision]
      if (!toStatus) return
      await candidatesApi.updateStatus(route.params.id, {
        to_status: toStatus,
        reason: `HR 决策：${decision}`,
        operator_name: null
      })
      await refreshFlow()
      ElMessage.success(`已标记为${decision}`)
      return
    }

    await interviewRoundsApi.decide(route.params.id, round.id, { decision })
    await refreshFlow()
    ElMessage.success(`已标记为${decision}`)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '保存决策失败')
  }
}

const reopenFlow = async () => {
  try {
    await interviewRoundsApi.reopen(route.params.id)
    await refreshFlow()
    ElMessage.success('流程已重新打开')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '重新打开流程失败')
  }
}

const scrollToRecords = () => {
  activeTab.value = 'interview'
}

const generateInterviewQuestions = async () => {
  if (!canGenerateQuestions.value) {
    ElMessage.warning(questionMissingReason.value || '当前资料不完整，不能生成面试问题')
    return
  }
  questionGenerateLoading.value = true
  aiOverlayTitle.value = `正在生成${currentQuestionTypeLabel.value}`
  aiOverlayStages.value = ['读取岗位 JD', '分析简历特征', '匹配问题维度', `生成${currentQuestionTypeLabel.value}`]
  aiOverlayProgress.value = 10
  aiOverlayVisible.value = true

  setTimeout(() => { aiOverlayProgress.value = 30 }, 600)
  setTimeout(() => { aiOverlayProgress.value = 55 }, 1800)
  setTimeout(() => { aiOverlayProgress.value = 80 }, 3500)

  try {
    const response = await interviewQuestionsApi.generate(route.params.id, {
      requestId: null,
      roundType: currentQuestionType.value,
      roundNo: currentRound.value?.round_no ?? candidate.value?.current_round_no ?? 1,
      forceRegenerate: true
    })
    const report = response.data
    questionHistory.value = [
      report,
      ...questionHistory.value.filter(item => item.id !== report.id)
    ].sort((a, b) => String(b.created_at || '').localeCompare(String(a.created_at || '')))
    viewingQuestionReport.value = null
    showAllQuestionHistory.value = false
    await fetchQuestionStats()
    aiOverlayProgress.value = 100
    setTimeout(() => {
      aiOverlayVisible.value = false
      activeTab.value = 'questions'
      ElMessage.success(`${currentQuestionTypeLabel.value}已生成`)
    }, 500)
  } catch (error) {
    aiOverlayVisible.value = false
    ElMessage.error(error.response?.data?.detail || '生成面试问题失败')
  } finally {
    questionGenerateLoading.value = false
  }
}

const goBack = () => {
  router.push(route.query.from === 'interviews' ? '/interviews' : '/candidates')
}

const applyRouteTab = () => {
  const tab = Array.isArray(route.query.tab) ? route.query.tab[0] : route.query.tab
  if (validDetailTabs.has(tab)) activeTab.value = tab
}

watch(() => route.query.tab, applyRouteTab)

watch(currentQuestionType, async () => {
  // 问题类型变化时，清空当前查看的报告（除非与当前类型一致）
  if (viewingQuestionReport.value && viewingQuestionReport.value.round_type !== currentQuestionType.value) {
    viewingQuestionReport.value = null
  }
  showAllQuestionHistory.value = false
  await fetchQuestionStats()
})

onMounted(async () => {
  applyRouteTab()
  await Promise.all([fetchCandidate(), fetchResumeScreeningReport(), fetchInterviewRounds(), fetchInterviewQuestions()])
  await fetchQuestionStats()
})
</script>

<style scoped>
:global(body) {
  background: var(--color-bg);
}

.candidate-detail {
  max-width: 1200px;
  margin: 0 auto;
  color: var(--color-text);
}

.candidate-detail :deep(.page-card),
.page-card {
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  box-shadow: var(--shadow-card);
  background: var(--color-surface);
}

.detail-header {
  display: flex;
  align-items: center;
  min-height: 36px;
  margin-bottom: 14px;
}

.back-button {
  color: var(--color-text-secondary);
  padding-left: 0;
}

.decision-hero {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(360px, 1.25fr) 240px;
  gap: 24px;
  align-items: center;
  padding: 24px;
  margin-bottom: 20px;
}

.candidate-title-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.candidate-name {
  margin: 0;
  font-size: 28px;
  line-height: 1.2;
  font-weight: var(--font-bold);
  color: var(--color-text);
  letter-spacing: 0;
}

.candidate-meta {
  display: flex;
  gap: 10px 14px;
  flex-wrap: wrap;
  align-items: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.meta-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.meta-pill {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

.hero-advice {
  display: grid;
  grid-template-columns: 104px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
  min-width: 0;
}

.score-block {
  width: 104px;
  height: 104px;
  border-radius: var(--radius-lg);
  background: var(--color-gray-50);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.score-number {
  font-size: 42px;
  line-height: 1;
  font-weight: var(--font-bold);
}

.score-label {
  margin-top: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
}

.advice-copy {
  min-width: 0;
}

.advice-line {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 15px;
  font-weight: var(--font-bold);
}

.advice-line span,
.next-meta span,
.meta-lbl {
  color: var(--color-text-secondary);
  font-weight: var(--font-semibold);
}

.advice-summary {
  margin: 0;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.7;
}

.ai-disclaimer {
  margin: 8px 0 0;
  color: var(--color-amber);
  font-size: 12px;
}

.hero-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.pill-button {
  width: 100%;
  height: 44px;
  margin-left: 0 !important;
  border-radius: 999px;
  font-weight: var(--font-bold);
  transition: transform 0.16s ease, box-shadow 0.16s ease, background-color 0.16s ease, border-color 0.16s ease;
}

.pill-button:hover {
  transform: translateY(-1px);
}

.pill-button.primary {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: var(--color-surface);
  box-shadow: 0 8px 18px rgba(15, 118, 110, 0.18);
}

.pill-button.primary:hover {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
  box-shadow: 0 12px 24px rgba(15, 118, 110, 0.22);
}

.pill-button.secondary {
  background: var(--color-surface);
  border-color: var(--color-border-strong);
  color: var(--color-text);
}

.pill-button.danger {
  background: var(--color-red-soft);
  border-color: var(--color-red-soft);
  color: var(--color-red);
}

.detail-tabs {
  margin-top: 4px;
}

.detail-tabs :deep(.el-tabs__header) {
  margin: 0 0 20px;
}

.detail-tabs :deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background: var(--color-border);
}

.detail-tabs :deep(.el-tabs__item) {
  height: 44px;
  padding: 0 22px;
  color: var(--color-text-secondary);
  font-weight: var(--font-bold);
}

.detail-tabs :deep(.el-tabs__item.is-active) {
  color: var(--color-primary);
}

.detail-tabs :deep(.el-tabs__active-bar) {
  background: var(--color-primary);
}

.overview-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: 20px;
  align-items: start;
}

.overview-main,
.interview-flow {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-card,
.next-step-card,
.empty-interview-card {
  padding: 24px;
}

.next-step-card {
  position: sticky;
  top: 92px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.section-title {
  margin: 0;
  font-size: 18px;
  font-weight: var(--font-bold);
  color: var(--color-text);
}

.section-desc {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.decision-summary-grid {
  display: grid;
  grid-template-columns: 118px minmax(0, 1fr);
  gap: 18px;
  align-items: center;
}

.summary-score {
  height: 118px;
  border-radius: var(--radius-lg);
  background: var(--color-gray-50);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.summary-score strong {
  font-size: 40px;
  line-height: 1;
}

.summary-score span,
.summary-copy span {
  color: var(--color-text-secondary);
  font-size: 13px;
}

.summary-copy {
  display: flex;
  flex-direction: column;
  gap: 10px;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.6;
}

.risk-tags {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.brief-list {
  display: grid;
  gap: 12px;
}

.brief-list.two-col {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.brief-item {
  padding: 14px 16px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.65;
}

.brief-item strong {
  display: block;
  margin-bottom: 4px;
  font-size: 14px;
}

.brief-item p {
  margin: 0;
  color: var(--color-text-secondary);
}

.brief-item.success {
  background: var(--color-green-soft);
}

.brief-item.warning {
  background: var(--color-amber-soft);
}

.brief-item.danger-soft {
  background: var(--color-red-soft);
}

.next-meta {
  display: grid;
  gap: 12px;
  margin: 18px 0 20px;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.55;
}

.next-meta div {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.report-link {
  height: 32px;
  padding: 0;
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

.report-link:hover {
  color: var(--color-primary-hover);
}

.empty-interview-card {
  min-height: 220px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 12px;
}

.empty-interview-card h3,
.empty-panel h3 {
  margin: 0;
  font-size: 20px;
  color: var(--color-text);
}

.empty-interview-card p,
.empty-panel p {
  margin: 0 0 8px;
  color: var(--color-text-secondary);
}

.questions-tab-card {
  display: grid;
  gap: 18px;
}

.question-header {
  align-items: center;
}

.question-actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  align-items: center;
}

.current-round-type-hint {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 40px;
  padding: 0 16px;
  border-radius: var(--radius-sm);
  background: var(--color-gray-50);
  border: 1px solid var(--color-border);
}

.hint-label {
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: var(--font-semibold);
}

.hint-value {
  color: var(--color-primary);
  font-size: 14px;
  font-weight: var(--font-bold);
}

.question-generate-button {
  min-width: 132px;
  height: 40px;
  border-radius: var(--radius-sm);
  font-weight: var(--font-bold);
  background: var(--color-primary);
  border-color: var(--color-primary);
}

.question-source-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px;
}

.question-source-grid > div {
  min-height: 72px;
  padding: 12px 14px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
}

.question-source-grid span {
  display: block;
  margin-bottom: 8px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: var(--font-semibold);
}

.question-source-grid strong {
  display: block;
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.5;
  word-break: break-word;
}

.question-workspace {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 20px;
  align-items: start;
}

.question-main-panel,
.question-side-panel {
  min-width: 0;
}

.question-side-panel {
  display: grid;
  gap: 20px;
}

.question-history-select-row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 38px;
  margin-bottom: 12px;
  padding: 8px 10px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
}

.question-history-select-row > span {
  flex: 0 0 auto;
  color: var(--color-gray-700);
  font-size: 13px;
  font-weight: var(--font-bold);
}

.question-history-select-row :deep(.el-select) {
  flex: 1;
  min-width: 0;
}

.subsection-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.subsection-header.compact {
  margin-bottom: 10px;
}

.subsection-header h4 {
  margin: 0;
  color: var(--color-text);
  font-size: 15px;
  font-weight: var(--font-bold);
}

.subsection-header p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.empty-stats {
  min-height: 70px;
  display: flex;
  align-items: center;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.question-stats-list {
  display: grid;
  gap: 10px;
}

.question-stat-item {
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 10px;
  align-items: flex-start;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-border);
}

.question-stat-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.stat-rank {
  width: 24px;
  height: 24px;
  border-radius: var(--radius-sm);
  background: var(--color-gray-50);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: var(--font-bold);
}

.question-stat-item strong {
  display: block;
  color: var(--color-text);
  font-size: 13px;
  line-height: 1.55;
}

.question-stat-item p {
  margin: 4px 0 0;
  color: var(--color-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

.generated-question-list {
  display: grid;
  gap: 12px;
}

.generated-question-card {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr);
  gap: 14px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.question-index {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--color-primary-soft);
  color: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: var(--font-bold);
}

.question-content {
  min-width: 0;
}

.question-title-row {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}

.question-title-row h4 {
  margin: 0;
  color: var(--color-text);
  font-size: 15px;
  line-height: 1.55;
}

.question-content p {
  margin: 8px 0 0;
  color: var(--color-gray-700);
  font-size: 13px;
  line-height: 1.7;
}

.question-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.question-meta span {
  padding: 5px 8px;
  border-radius: var(--radius-sm);
  background: var(--color-gray-50);
  color: var(--color-gray-700);
  font-size: 12px;
  line-height: 1.4;
}

.round-current-card {
  background: linear-gradient(180deg, var(--color-surface) 0%, var(--color-primary-50) 100%);
}

.round-current-head,
.round-card-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 16px;
}

.eyebrow {
  display: block;
  margin-bottom: 6px;
  color: var(--color-primary);
  font-size: 12px;
  font-weight: var(--font-bold);
}

.round-current-head h3,
.round-card-head h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 20px;
}

.round-current-head p,
.round-card-head p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
}

.round-meta-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.round-meta-grid > div,
.evaluation-grid > div {
  min-height: 64px;
  padding: 12px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  color: var(--color-text);
  font-size: 14px;
  font-weight: var(--font-bold);
}

.round-meta-grid span,
.evaluation-grid span {
  display: block;
  margin-bottom: 6px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: var(--font-semibold);
}

.round-record,
.evaluation-grid {
  margin-top: 16px;
}

.round-record h4 {
  margin: 0 0 10px;
  color: var(--color-text);
  font-size: 15px;
}

.round-record p {
  margin: 0;
  color: var(--color-gray-700);
  font-size: 14px;
  line-height: 1.7;
}

.evaluation-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.evaluation-grid strong {
  color: var(--color-text);
  font-size: 16px;
}

.report-header {
  display: flex;
  gap: 24px;
  align-items: center;
  margin-bottom: 20px;
  padding: 18px;
  border-radius: var(--radius-lg);
  background: var(--color-gray-50);
}

.report-score-big {
  min-width: 92px;
  font-size: 42px;
  font-weight: var(--font-bold);
  line-height: 1;
}

.score-unit {
  color: var(--color-text-secondary);
  font-size: 14px;
  font-weight: var(--font-medium);
}

.report-meta {
  display: grid;
  gap: 8px;
  color: var(--color-text);
  font-size: 14px;
}

.report-collapse :deep(.el-collapse-item__header) {
  height: 52px;
  color: var(--color-text);
  font-weight: var(--font-bold);
  font-size: 15px;
}

.collapse-text,
.resume-text {
  margin: 0;
  padding: 16px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
  color: var(--color-gray-700);
  font-size: 14px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.empty-panel {
  min-height: 180px;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: center;
  gap: 10px;
  padding: 20px;
  border-radius: var(--radius-lg);
  background: var(--color-gray-50);
}

.logs-card :deep(.el-timeline) {
  padding-left: 2px;
}

.timeline-title {
  color: var(--color-text);
  font-size: 15px;
  font-weight: var(--font-bold);
}

.timeline-desc {
  margin-top: 5px;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.dialog-alert {
  margin-bottom: 16px;
}

.record-dialog-header {
  padding-right: 36px;
}

.record-dialog-header h2 {
  margin: 0;
  color: var(--color-text);
  font-size: 20px;
  font-weight: var(--font-bold);
  line-height: 1.35;
}

.record-dialog-header p {
  margin: 8px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

:deep(.record-dialog .el-dialog__body) {
  padding-top: 8px;
}

.record-dialog-body {
  max-height: min(68vh, 680px);
  overflow-y: auto;
  display: grid;
  gap: 16px;
  padding-right: 4px;
}

.record-context-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--color-primary-soft);
  border-radius: var(--radius-md);
  background: var(--color-primary-50);
}

.record-context-strip div {
  min-width: 0;
}

.record-context-strip span {
  display: block;
  margin-bottom: 4px;
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: var(--font-semibold);
}

.record-context-strip strong {
  display: block;
  overflow: hidden;
  color: var(--color-text);
  font-size: 13px;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-stepper {
  display: flex;
  align-items: center;
  gap: 10px;
  overflow-x: auto;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  background: var(--color-gray-50);
}

.record-step,
.step-arrow {
  flex: 0 0 auto;
}

.record-step {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
  font-weight: var(--font-semibold);
  white-space: nowrap;
}

.record-step span {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--color-gray-100);
  color: var(--color-gray-700);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: var(--font-bold);
}

.record-step.active {
  color: var(--color-primary);
}

.record-step.active span {
  background: var(--color-primary);
  color: var(--color-surface);
}

.step-arrow {
  color: var(--color-text-muted);
  font-size: 13px;
}

.record-input-section {
  display: grid;
  gap: 12px;
  padding: 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  background: var(--color-surface);
}

.record-section-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
}

.record-section-head h3 {
  margin: 0;
  color: var(--color-text);
  font-size: 16px;
  font-weight: var(--font-bold);
}

.record-section-head p {
  margin: 6px 0 0;
  color: var(--color-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.record-upload-area {
  flex: 0 0 auto;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
}

.upload-placeholder-button {
  border-color: var(--color-primary);
  background: var(--color-primary-50);
  color: var(--color-primary);
  font-weight: var(--font-bold);
}

.upload-placeholder-button:hover {
  border-color: var(--color-primary-hover);
  background: var(--color-primary-soft);
  color: var(--color-primary-hover);
}

.record-upload-area span {
  color: var(--color-text-muted);
  font-size: 12px;
  line-height: 1.4;
}

.record-textarea :deep(.el-textarea__inner) {
  min-height: 248px;
  border-radius: var(--radius-sm);
  color: var(--color-text);
  font-size: 14px;
  line-height: 1.75;
}

.record-optional-collapse {
  border-top: 1px solid var(--color-border);
  border-bottom: 1px solid var(--color-border);
}

.record-optional-collapse :deep(.el-collapse-item__header) {
  height: auto;
  min-height: 58px;
}

.manual-collapse-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 0;
  line-height: 1.4;
}

.manual-collapse-title strong {
  color: var(--color-text);
  font-size: 14px;
}

.manual-collapse-title span {
  color: var(--color-text-secondary);
  font-size: 12px;
  font-weight: var(--font-medium);
}

.manual-info-form {
  padding-top: 4px;
}

.record-dialog-footer {
  width: 100%;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.record-footer-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.generate-record-button {
  min-width: 132px;
  background: var(--color-primary);
  border-color: var(--color-primary);
  font-weight: var(--font-bold);
}

.generate-record-button:hover,
.generate-record-button:focus {
  background: var(--color-primary-hover);
  border-color: var(--color-primary-hover);
}

@media (max-width: 1100px) {
  .decision-hero,
  .overview-layout,
  .question-workspace {
    grid-template-columns: 1fr;
  }

  .hero-actions,
  .hero-actions .pill-button {
    width: auto;
    min-width: 150px;
  }

  .next-step-card {
    position: static;
  }

  .question-source-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 760px) {
  .candidate-detail {
    max-width: 100%;
  }

  .decision-hero,
  .content-card,
  .next-step-card,
  .empty-interview-card {
    padding: 18px;
  }

  .hero-advice,
  .decision-summary-grid,
  .question-source-grid,
  .round-meta-grid,
  .evaluation-grid,
  .brief-list.two-col {
    grid-template-columns: 1fr;
  }

  .hero-actions .pill-button {
    width: 100%;
  }

  .section-header,
  .question-title-row,
  .round-current-head,
  .round-card-head,
  .report-header {
    flex-direction: column;
    align-items: stretch;
  }

  .question-actions,
  .question-generate-button {
    width: 100%;
  }

  .current-round-type-hint {
    width: 100%;
    justify-content: center;
  }

  .question-history-select-row {
    align-items: stretch;
    flex-direction: column;
  }

  :deep(.record-dialog) {
    width: calc(100vw - 32px) !important;
  }

  .record-context-strip {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .record-section-head,
  .record-dialog-footer,
  .record-footer-actions {
    align-items: stretch;
    flex-direction: column;
  }

  .record-upload-area {
    align-items: flex-start;
  }

  :deep(.el-col) {
    max-width: 100%;
    flex: 0 0 100%;
  }
}
</style>
