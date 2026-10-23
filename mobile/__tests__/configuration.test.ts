import { validateApiUrl } from '@/config/validateEnv';
import { formatDecimal, isBalanceResponse } from '@/features/banking/contracts';

test('accepts emulator and LAN addresses with the versioned API prefix', () => {
  expect(validateApiUrl('http://10.0.2.2:8000/api/v1/')).toBe('http://10.0.2.2:8000/api/v1');
  expect(validateApiUrl('http://192.168.0.10:8000/api/v1')).toContain('192.168.0.10');
});
test.each([undefined, '', 'broken', 'file:///api/v1', 'http://a:b@localhost/api/v1', 'http://localhost/api/v1?token=secret', 'http://localhost/wrong'])('rejects unsafe/malformed public config %s', value => {
  expect(() => validateApiUrl(value)).toThrow();
});
test('money formatting keeps exact precision above the safe integer range', () => {
  expect(formatDecimal('9999999999999999.99')).toBe('R$ 9.999.999.999.999.999,99');
  expect(formatDecimal('-0.29')).toBe('−R$ 0,29');
  expect(isBalanceResponse({ account_id: 'a', currency: 'BRL', balance: 0 }, 'a')).toBe(false);
  expect(isBalanceResponse({ account_id: 'a', currency: 'BRL', balance: '0.00' }, 'a')).toBe(true);
});
