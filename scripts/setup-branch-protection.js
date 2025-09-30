#!/usr/bin/env node

const requiredChecks = [
  'backend-ci',
  'frontend-ci', 
  'openapi-verify',
  'post-deploy-health-assertions',
  'orchestrator-e2e'
]

const branchProtectionConfig = {
  required_status_checks: {
    strict: true,
    contexts: requiredChecks
  },
  enforce_admins: false,
  required_pull_request_reviews: {
    required_approving_review_count: 1,
    dismiss_stale_reviews: true,
    require_code_owner_reviews: false
  },
  restrictions: null,
  allow_force_pushes: false,
  allow_deletions: false
}

console.log('🛡️ Branch Protection Configuration for main branch:')
console.log('📋 Required status checks:')
requiredChecks.forEach(check => console.log(`   - ${check}`))

console.log('\n⚙️ Configuration:')
console.log(`   - Strict status checks: ${branchProtectionConfig.required_status_checks.strict}`)
console.log(`   - Required reviews: ${branchProtectionConfig.required_pull_request_reviews.required_approving_review_count}`)
console.log(`   - Dismiss stale reviews: ${branchProtectionConfig.required_pull_request_reviews.dismiss_stale_reviews}`)
console.log(`   - Allow force pushes: ${branchProtectionConfig.allow_force_pushes}`)

console.log('\n🚀 To apply this configuration, run:')
console.log('gh api repos/RC918/morningai/branches/main/protection -X PUT --input - <<EOF')
console.log(JSON.stringify(branchProtectionConfig, null, 2))
console.log('EOF')

console.log('\n📝 Or save to file and apply:')
console.log('echo \'' + JSON.stringify(branchProtectionConfig, null, 2) + '\' > branch-protection.json')
console.log('gh api repos/RC918/morningai/branches/main/protection -X PUT --input branch-protection.json')
