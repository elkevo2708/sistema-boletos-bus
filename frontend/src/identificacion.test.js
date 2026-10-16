import assert from 'node:assert/strict';
import test from 'node:test';
import { cedulaValida, identificacionValida, rucValido, validarIdentificacion } from './identificacion.js';

test('cédula módulo 10', () => {
  assert.equal(cedulaValida('1710034065'), true);
  assert.equal(cedulaValida('1710034066'), false);
  assert.equal(cedulaValida('0010034065'), false);
  assert.equal(cedulaValida('1760034065'), false);
  assert.equal(cedulaValida('3010034068'), true);
  assert.equal(validarIdentificacion('cedula', '1710034065'), null);
});

test('RUC natural, privado y público', () => {
  assert.equal(rucValido('1710034065001'), true);
  assert.equal(rucValido('1710034065000'), false);
  assert.equal(rucValido('1790012344001'), true);
  assert.equal(rucValido('1790012345001'), false);
  assert.equal(rucValido('1760001200001'), true);
  assert.equal(rucValido('1760001200000'), false);
});

test('pasaporte y consumidor final', () => {
  assert.equal(identificacionValida('pasaporte', 'AB123456'), true);
  assert.equal(identificacionValida('pasaporte', 'A1'), false);
  assert.equal(identificacionValida('consumidor_final', '9999999999999'), true);
  assert.equal(identificacionValida('consumidor_final', '1710034065'), false);
});
