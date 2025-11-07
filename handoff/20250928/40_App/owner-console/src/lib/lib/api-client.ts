/**
 * Re-export of apiClient for Orval-generated clients
 * This ensures generated clients import from '../../lib/api-client'
 * which matches the test mock path vi.mock('../../lib/api-client')
 */
export { apiClient } from '../api-client';
