import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle, 
  Badge, 
  Button, 
  Alert, 
  AlertDescription, 
  AlertTitle, 
  Skeleton,
  Input,
  Label,
  Textarea,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Switch,
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  SectionCard
} from '@morningai/shared-ui'
import { 
  Shield,
  ShieldCheck,
  ShieldX,
  Filter,
  Gauge,
  Clock,
  Cpu,
  RefreshCw, 
  Plus,
  Pencil,
  Trash2,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileJson,
  ChevronRight
} from 'lucide-react'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  getPolicyTemplates, 
  listPolicies, 
  getPolicy,
  createPolicy, 
  updatePolicy, 
  deletePolicy 
} from '@/lib/ai-policies-api'

const POLICY_TYPE_ICONS = {
  capability_whitelist: ShieldCheck,
  capability_blacklist: ShieldX,
  content_filter: Filter,
  usage_limit: Gauge,
  rate_limit: Clock,
  model_restriction: Cpu
}

const POLICY_TYPE_COLORS = {
  capability_whitelist: 'bg-growth-10 text-growth border-growth-300',
  capability_blacklist: 'bg-error-10 text-error border-error-300',
  content_filter: 'bg-wisdom-10 text-wisdom border-wisdom-300',
  usage_limit: 'bg-energy-10 text-energy border-energy-300',
  rate_limit: 'bg-calm-10 text-calm border-calm-300',
  model_restriction: 'bg-joy-10 text-joy border-joy-300'
}

const STATUS_COLORS = {
  active: 'bg-growth-10 text-growth border-growth-300',
  inactive: 'bg-neutral-100 text-neutral-600 border-neutral-300',
  draft: 'bg-warning-10 text-warning border-warning-300'
}

const AIPolicies = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [policies, setPolicies] = useState([])
  const [templates, setTemplates] = useState({})
  const [selectedPolicy, setSelectedPolicy] = useState(null)
  const [isCreating, setIsCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [editorError, setEditorError] = useState(null)
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false)
  const [policyToDelete, setPolicyToDelete] = useState(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const [templatesRes, policiesRes] = await Promise.all([
        getPolicyTemplates(),
        listPolicies()
      ])
      
      setTemplates(templatesRes.templates || {})
      setPolicies(policiesRes.policies || [])
    } catch (err) {
      console.error('Failed to load policies:', err)
      setError(err.message || t('aiPolicies.error.loadFailed'))
    } finally {
      setLoading(false)
    }
  }

  const handleCreateNew = () => {
    setSelectedPolicy(null)
    setIsCreating(true)
    setEditorError(null)
  }

  const handleSelectPolicy = async (policy) => {
    try {
      const fullPolicy = await getPolicy(policy.id)
      setSelectedPolicy(fullPolicy)
      setIsCreating(false)
      setEditorError(null)
    } catch (err) {
      console.error('Failed to load policy:', err)
      setEditorError(err.message || t('aiPolicies.error.loadFailed'))
    }
  }

  const handleSavePolicy = async (policyData) => {
    try {
      setSaving(true)
      setEditorError(null)
      
      if (isCreating) {
        await createPolicy(policyData)
      } else if (selectedPolicy) {
        await updatePolicy(selectedPolicy.id, policyData)
      }
      
      await loadData()
      setIsCreating(false)
      setSelectedPolicy(null)
    } catch (err) {
      console.error('Failed to save policy:', err)
      setEditorError(err.message || t('aiPolicies.error.saveFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handleDeletePolicy = async () => {
    if (!policyToDelete) return
    
    try {
      setSaving(true)
      await deletePolicy(policyToDelete.id)
      await loadData()
      setDeleteDialogOpen(false)
      setPolicyToDelete(null)
      if (selectedPolicy?.id === policyToDelete.id) {
        setSelectedPolicy(null)
      }
    } catch (err) {
      console.error('Failed to delete policy:', err)
      setEditorError(err.message || t('aiPolicies.error.deleteFailed'))
    } finally {
      setSaving(false)
    }
  }

  const handleCancelEdit = () => {
    setIsCreating(false)
    setSelectedPolicy(null)
    setEditorError(null)
  }

  const formatDate = (dateString) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleDateString()
  }

  if (loading && policies.length === 0) {
    return (
      <div className="space-y-8" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        <div className="flex items-center justify-between">
          <div>
            <Skeleton className="h-7 w-64 mb-2" aria-hidden="true" />
            <Skeleton className="h-5 w-96" aria-hidden="true" />
          </div>
          <Skeleton className="h-10 w-32" aria-hidden="true" />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <Skeleton className="h-6 w-32" aria-hidden="true" />
              </div>
              <div className="p-5 space-y-3">
                {[1, 2, 3].map((i) => (
                  <Skeleton key={i} className="h-16 w-full" aria-hidden="true" />
                ))}
              </div>
            </div>
          </div>
          <div className="lg:col-span-2">
            <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card">
              <div className="px-5 py-4 border-b border-[var(--border)]">
                <Skeleton className="h-6 w-48" aria-hidden="true" />
              </div>
              <div className="p-5 space-y-4">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" aria-hidden="true" />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8" aria-busy={loading} data-testid="ai-policies">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-[var(--text-primary)]">
            {t('aiPolicies.title')}
          </h1>
          <p className="text-sm text-[var(--text-secondary)] mt-1">
            {t('aiPolicies.subtitle')}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <AppleButton onClick={loadData} variant="outline" haptic="light" disabled={loading}>
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            {t('aiPolicies.refresh')}
          </AppleButton>
          <AppleButton onClick={handleCreateNew} haptic="medium">
            <Plus className="w-4 h-4 mr-2" />
            {t('aiPolicies.newPolicy')}
          </AppleButton>
        </div>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button onClick={loadData} variant="outline" size="sm" className="ml-4">
              {t('common.retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-1">
          <SectionCard
            title={t('aiPolicies.list.title')}
            subtitle={t('aiPolicies.list.policyCount', { count: policies.length })}
            action={<FileJson className="w-5 h-5 text-[var(--text-secondary)]" />}
            data-testid="policy-list"
          >
            {policies.length === 0 ? (
              <div className="py-8 text-center">
                <Shield className="w-12 h-12 text-[var(--text-secondary)] mx-auto mb-4" />
                <p className="text-sm text-[var(--text-secondary)]">
                  {t('aiPolicies.list.empty')}
                </p>
              </div>
            ) : (
              <div className="space-y-2">
                {policies.map((policy) => {
                  const Icon = POLICY_TYPE_ICONS[policy.policy_type] || Shield
                  const isSelected = selectedPolicy?.id === policy.id
                  
                  return (
                    <div
                      key={policy.id}
                      role="button"
                      tabIndex={0}
                      onClick={() => handleSelectPolicy(policy)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleSelectPolicy(policy)
                        }
                      }}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        isSelected
                          ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                          : 'border-[var(--border)] hover:border-neutral-300 dark:hover:border-neutral-600'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${POLICY_TYPE_COLORS[policy.policy_type] || 'bg-neutral-100'}`}>
                            <Icon className="w-4 h-4" />
                          </div>
                          <div>
                            <p className="font-medium text-sm truncate max-w-[150px]">
                              {policy.name}
                            </p>
                            <p className="text-xs text-[var(--text-secondary)]">
                              {t(`aiPolicies.types.${policy.policy_type}.title`, policy.policy_type)}
                            </p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={STATUS_COLORS[policy.status] || STATUS_COLORS.draft}>
                            {t(`aiPolicies.status.${policy.status}`, policy.status)}
                          </Badge>
                          <ChevronRight className="w-4 h-4 text-[var(--text-secondary)]" />
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            )}
          </SectionCard>
        </div>

        <div className="lg:col-span-2">
          {(isCreating || selectedPolicy) ? (
            <PolicyEditor
              templates={templates}
              policy={selectedPolicy}
              isCreating={isCreating}
              saving={saving}
              error={editorError}
              onSave={handleSavePolicy}
              onCancel={handleCancelEdit}
              onDelete={(policy) => {
                setPolicyToDelete(policy)
                setDeleteDialogOpen(true)
              }}
            />
          ) : (
            <SectionCard
              title={t('aiPolicies.editor.selectType')}
              subtitle={t('aiPolicies.subtitle')}
              data-testid="policy-editor-empty"
            >
              <div className="py-8 text-center">
                <Shield className="w-16 h-16 text-[var(--text-secondary)] mx-auto mb-4" />
                <AppleButton onClick={handleCreateNew} haptic="medium">
                  <Plus className="w-4 h-4 mr-2" />
                  {t('aiPolicies.newPolicy')}
                </AppleButton>
              </div>
            </SectionCard>
          )}
        </div>
      </div>

      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{t('aiPolicies.editor.delete')}</DialogTitle>
            <DialogDescription>
              {t('aiPolicies.editor.deleteConfirm')}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setDeleteDialogOpen(false)}>
              {t('aiPolicies.editor.cancel')}
            </Button>
            <Button variant="destructive" onClick={handleDeletePolicy} disabled={saving}>
              {t('aiPolicies.editor.delete')}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

const PolicyEditor = ({ templates, policy, isCreating, saving, error, onSave, onCancel, onDelete }) => {
  const { t } = useTranslation()
  const [name, setName] = useState(policy?.name || '')
  const [description, setDescription] = useState(policy?.description || '')
  const [policyType, setPolicyType] = useState(policy?.policy_type || '')
  const [status, setStatus] = useState(policy?.status || 'draft')
  const [priority, setPriority] = useState(policy?.priority || 0)
  const [rules, setRules] = useState(policy?.rules || {})
  const [jsonMode, setJsonMode] = useState(false)
  const [jsonText, setJsonText] = useState('')
  const [jsonError, setJsonError] = useState(null)
  const [validationError, setValidationError] = useState(null)

  useEffect(() => {
    if (policy) {
      setName(policy.name || '')
      setDescription(policy.description || '')
      setPolicyType(policy.policy_type || '')
      setStatus(policy.status || 'draft')
      setPriority(policy.priority || 0)
      setRules(policy.rules || {})
      setJsonText(JSON.stringify(policy.rules || {}, null, 2))
    } else {
      setName('')
      setDescription('')
      setPolicyType('')
      setStatus('draft')
      setPriority(0)
      setRules({})
      setJsonText('{}')
    }
    setJsonError(null)
    setValidationError(null)
  }, [policy])

  useEffect(() => {
    if (policyType && templates[policyType] && !policy) {
      const templateRules = templates[policyType].rules || {}
      setRules(templateRules)
      setJsonText(JSON.stringify(templateRules, null, 2))
    }
  }, [policyType, templates, policy])

  const handleJsonChange = (value) => {
    setJsonText(value)
    try {
      const parsed = JSON.parse(value)
      setRules(parsed)
      setJsonError(null)
    } catch (err) {
      setJsonError(t('aiPolicies.validation.invalidJson', { message: err.message }))
    }
  }

  const handleRuleChange = (key, value) => {
    const newRules = { ...rules, [key]: value }
    setRules(newRules)
    setJsonText(JSON.stringify(newRules, null, 2))
  }

  const handleArrayRuleChange = (key, value) => {
    const items = value.split('\n').filter(item => item.trim())
    handleRuleChange(key, items)
  }

  const handleSubmit = () => {
    setValidationError(null)
    
    if (!name.trim()) {
      setValidationError(t('aiPolicies.validation.nameRequired'))
      return
    }
    
    if (!policyType) {
      setValidationError(t('aiPolicies.validation.rulesRequired'))
      return
    }
    
    if (jsonError) {
      return
    }
    
    onSave({
      name: name.trim(),
      description: description.trim(),
      policy_type: policyType,
      status,
      priority,
      rules
    })
  }

  const renderRuleField = (key, value) => {
    const fieldLabel = t(`aiPolicies.fields.${key}`, key.replace(/_/g, ' '))
    
    if (typeof value === 'boolean') {
      return (
        <div key={key} className="flex items-center justify-between py-2">
          <Label htmlFor={key} className="text-sm">{fieldLabel}</Label>
          <Switch
            id={key}
            checked={rules[key] ?? value}
            onCheckedChange={(checked) => handleRuleChange(key, checked)}
          />
        </div>
      )
    }
    
    if (typeof value === 'number') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-sm">{fieldLabel}</Label>
          <Input
            id={key}
            type="number"
            value={rules[key] ?? value}
            onChange={(e) => handleRuleChange(key, parseInt(e.target.value) || 0)}
          />
        </div>
      )
    }
    
    if (Array.isArray(value)) {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-sm">{fieldLabel}</Label>
          <Textarea
            id={key}
            value={(rules[key] || value).join('\n')}
            onChange={(e) => handleArrayRuleChange(key, e.target.value)}
            placeholder={t('aiPolicies.editor.rulesHelp')}
            rows={3}
          />
          <p className="text-xs text-[var(--text-secondary)]">{t('aiPolicies.editor.oneItemPerLine')}</p>
        </div>
      )
    }
    
    if (typeof value === 'string') {
      return (
        <div key={key} className="space-y-2">
          <Label htmlFor={key} className="text-sm">{fieldLabel}</Label>
          <Input
            id={key}
            value={rules[key] ?? value}
            onChange={(e) => handleRuleChange(key, e.target.value)}
          />
        </div>
      )
    }
    
    return null
  }

  const templateRules = policyType && templates[policyType] ? templates[policyType].rules : {}

  return (
    <div className="rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card" data-testid="policy-editor">
      <div className="px-5 py-4 border-b border-[var(--border)]">
        <h2 className="text-base font-semibold text-[var(--text-primary)] flex items-center gap-2">
          {isCreating ? (
            <>
              <Plus className="w-5 h-5" />
              {t('aiPolicies.editor.titleNew')}
            </>
          ) : (
            <>
              <Pencil className="w-5 h-5" />
              {t('aiPolicies.editor.titleEdit')}
            </>
          )}
        </h2>
      </div>
      <div className="p-5 space-y-6">
        {(error || validationError) && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error || validationError}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="name">{t('aiPolicies.editor.nameLabel')}</Label>
            <Input
              id="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('aiPolicies.editor.namePlaceholder')}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="status">{t('aiPolicies.editor.statusLabel')}</Label>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="draft">{t('aiPolicies.status.draft')}</SelectItem>
                <SelectItem value="active">{t('aiPolicies.status.active')}</SelectItem>
                <SelectItem value="inactive">{t('aiPolicies.status.inactive')}</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="description">{t('aiPolicies.editor.descriptionLabel')}</Label>
          <Textarea
            id="description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder={t('aiPolicies.editor.descriptionPlaceholder')}
            rows={2}
          />
        </div>

        <div className="space-y-3">
          <Label>{t('aiPolicies.editor.typeLabel')}</Label>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {Object.entries(templates).map(([type, template]) => {
              const Icon = POLICY_TYPE_ICONS[type] || Shield
              const isSelected = policyType === type
              const isDisabled = !isCreating && policy?.policy_type !== type
              
              return (
                <div
                  key={type}
                  role="button"
                  tabIndex={isDisabled ? -1 : 0}
                  onClick={() => !isDisabled && setPolicyType(type)}
                  onKeyDown={(e) => {
                    if (!isDisabled && (e.key === 'Enter' || e.key === ' ')) {
                      e.preventDefault()
                      setPolicyType(type)
                    }
                  }}
                  aria-disabled={isDisabled}
                  className={`p-3 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/20'
                      : isDisabled
                        ? 'border-neutral-200 bg-neutral-50 opacity-50 cursor-not-allowed'
                        : 'border-neutral-200 dark:border-neutral-700 hover:border-neutral-300'
                  }`}
                >
                    <div className="flex items-center gap-2 mb-1">
                      <div className={`w-6 h-6 rounded-full flex items-center justify-center ${POLICY_TYPE_COLORS[type] || 'bg-neutral-100'}`}>
                        <Icon className="w-3 h-3" />
                      </div>
                      <span className="font-medium text-xs">
                        {t(`aiPolicies.types.${type}.title`, template.name)}
                      </span>
                    </div>
                    <p className="text-xs text-[var(--text-secondary)] line-clamp-2">
                      {t(`aiPolicies.types.${type}.description`, template.description)}
                    </p>
                </div>
              )
            })}
          </div>
        </div>

        {policyType && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <Label>{t('aiPolicies.editor.rulesLabel')}</Label>
              <div className="flex items-center gap-2">
                <span className="text-xs text-[var(--text-secondary)]">
                  {t('aiPolicies.editor.jsonEditor')}
                </span>
                <Switch
                  checked={jsonMode}
                  onCheckedChange={setJsonMode}
                />
              </div>
            </div>

            {jsonMode ? (
              <div className="space-y-2">
                <Textarea
                  value={jsonText}
                  onChange={(e) => handleJsonChange(e.target.value)}
                  className="font-mono text-sm"
                  rows={12}
                />
                {jsonError && (
                  <p className="text-xs text-error">{jsonError}</p>
                )}
                <p className="text-xs text-[var(--text-secondary)]">
                  {t('aiPolicies.editor.jsonEditorHelp')}
                </p>
              </div>
            ) : (
              <div className="space-y-4 p-4 bg-neutral-50 dark:bg-neutral-800 rounded-lg">
                {Object.entries(templateRules).map(([key, value]) => 
                  renderRuleField(key, value)
                )}
              </div>
            )}
          </div>
        )}

        <div className="flex items-center justify-between pt-4 border-t">
          <div>
            {!isCreating && policy && (
              <Button
                variant="destructive"
                onClick={() => onDelete(policy)}
                disabled={saving}
              >
                <Trash2 className="w-4 h-4 mr-2" />
                {t('aiPolicies.editor.delete')}
              </Button>
            )}
          </div>
          <div className="flex items-center gap-3">
            <Button variant="outline" onClick={onCancel} disabled={saving}>
              {t('aiPolicies.editor.cancel')}
            </Button>
            <AppleButton onClick={handleSubmit} haptic="medium" disabled={saving || !!jsonError}>
              {saving ? t('aiPolicies.editor.saving') : t('aiPolicies.editor.save')}
            </AppleButton>
          </div>
        </div>
      </div>
    </div>
  )
}

export default AIPolicies
