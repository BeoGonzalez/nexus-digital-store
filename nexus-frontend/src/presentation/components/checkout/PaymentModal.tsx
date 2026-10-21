'use client';

import React, { useState } from 'react';
import { useCheckoutMutation } from '@/application/hooks/useCheckoutMutation';
import { PaymentMethodType } from '@/domain/models/payment';
import { CreateOrderDTO, OrderStatus, OrderResponse } from '@/domain/models/order';
import { X, CheckCircle, AlertCircle, CreditCard, Landmark, Loader2 } from 'lucide-react';

interface PaymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  orderPayload: CreateOrderDTO;
}

export const PaymentModal: React.FC<PaymentModalProps> = ({ isOpen, onClose, orderPayload }) => {
  const { mutate: submitOrder, isPending, error, isSuccess, data } = useCheckoutMutation();

  const [method, setMethod] = useState<PaymentMethodType>(PaymentMethodType.CREDIT_CARD);
  
  // Credit Card Form State
  const [cardNumber, setCardNumber] = useState('');
  const [expiry, setExpiry] = useState('');
  const [cvv, setCvv] = useState('');
  const [formErrors, setFormErrors] = useState<{ cardNumber?: string; expiry?: string; cvv?: string }>({});

  if (!isOpen) return null;

  const validateForm = () => {
    const errors: { cardNumber?: string; expiry?: string; cvv?: string } = {};
    if (method === PaymentMethodType.CREDIT_CARD || method === PaymentMethodType.DEBIT_CARD) {
      if (cardNumber.replace(/\s/g, '').length < 16) {
        errors.cardNumber = 'Número de tarjeta inválido (16 dígitos req.)';
      }
      if (!/^(0[1-9]|1[0-2])\/\d{2}$/.test(expiry)) {
        errors.expiry = 'Formato MM/YY requerido';
      }
      if (cvv.length < 3) {
        errors.cvv = 'CVV inválido';
      }
    }
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleCardNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value.replace(/\D/g, '');
    const formatted = val.replace(/(.{4})/g, '$1 ').trim();
    setCardNumber(formatted.substring(0, 19));
  };

  const handleExpiryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let val = e.target.value.replace(/\D/g, '');
    if (val.length >= 2) {
      val = val.substring(0, 2) + '/' + val.substring(2, 4);
    }
    setExpiry(val.substring(0, 5));
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (validateForm()) {
      // In a real app, we would tokenize the card here before sending orderPayload.
      submitOrder(orderPayload);
    }
  };

  if (isSuccess && data) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm animate-in fade-in duration-300">
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-8 max-w-md w-full shadow-2xl relative text-slate-100 flex flex-col items-center">
          <CheckCircle className="w-16 h-16 text-emerald-500 mb-4 animate-bounce" />
          <h2 className="text-2xl font-bold mb-2">¡Pago Exitoso!</h2>
          <p className="text-slate-400 text-center mb-6">Tu orden ha sido procesada y confirmada.</p>
          
          <div className="w-full bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700/50">
            <div className="flex justify-between mb-2">
              <span className="text-slate-400">Orden ID</span>
              <span className="font-mono text-sm">{data.id.substring(0, 8)}...</span>
            </div>
            <div className="flex justify-between mb-2">
              <span className="text-slate-400">Total pagado</span>
              <span className="font-semibold text-emerald-400">
                ${data.totalAmountClp.toLocaleString('es-CL')}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Estado</span>
              <span className="text-sm px-2 py-0.5 rounded-full bg-emerald-500/20 text-emerald-300">
                {data.status}
              </span>
            </div>
          </div>
          
          <button 
            onClick={onClose}
            className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg font-medium transition-colors"
          >
            Volver a la tienda
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 max-w-lg w-full shadow-2xl relative text-slate-100">
        <button 
          onClick={onClose} 
          disabled={isPending}
          className="absolute top-4 right-4 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
        >
          <X className="w-6 h-6" />
        </button>
        
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
          Finalizar Compra
        </h2>

        {error && (
          <div className="mb-6 p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex items-start gap-3 text-red-400">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="text-sm">
              <p className="font-semibold">Ocurrió un error al procesar tu pago</p>
              <p className="opacity-90">{error.message || 'Por favor, intenta nuevamente.'}</p>
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Selector de Método */}
          <div className="grid grid-cols-2 gap-3">
            <button
              type="button"
              onClick={() => setMethod(PaymentMethodType.CREDIT_CARD)}
              className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                method === PaymentMethodType.CREDIT_CARD 
                  ? 'bg-blue-500/10 border-blue-500 text-blue-400' 
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              <CreditCard className="w-6 h-6" />
              <span className="text-sm font-medium">Tarjeta de Crédito/Débito</span>
            </button>
            
            <button
              type="button"
              onClick={() => setMethod(PaymentMethodType.TRANSFER)}
              className={`p-4 rounded-xl border flex flex-col items-center gap-2 transition-all ${
                method === PaymentMethodType.TRANSFER 
                  ? 'bg-blue-500/10 border-blue-500 text-blue-400' 
                  : 'bg-slate-800/50 border-slate-700 text-slate-400 hover:bg-slate-800'
              }`}
            >
              <Landmark className="w-6 h-6" />
              <span className="text-sm font-medium">Transferencia</span>
            </button>
          </div>

          {/* Formulario de Tarjeta */}
          {(method === PaymentMethodType.CREDIT_CARD || method === PaymentMethodType.DEBIT_CARD) && (
            <div className="space-y-4 animate-in slide-in-from-top-4 fade-in duration-300">
              <div className="space-y-1.5">
                <label className="text-sm font-medium text-slate-300">Número de Tarjeta</label>
                <input 
                  type="text" 
                  value={cardNumber}
                  onChange={handleCardNumberChange}
                  placeholder="0000 0000 0000 0000"
                  className={`w-full bg-slate-950 border ${formErrors.cardNumber ? 'border-red-500/50' : 'border-slate-800'} rounded-lg px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all`}
                />
                {formErrors.cardNumber && <p className="text-xs text-red-400">{formErrors.cardNumber}</p>}
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-300">Vencimiento</label>
                  <input 
                    type="text" 
                    value={expiry}
                    onChange={handleExpiryChange}
                    placeholder="MM/YY"
                    className={`w-full bg-slate-950 border ${formErrors.expiry ? 'border-red-500/50' : 'border-slate-800'} rounded-lg px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all`}
                  />
                  {formErrors.expiry && <p className="text-xs text-red-400">{formErrors.expiry}</p>}
                </div>
                
                <div className="space-y-1.5">
                  <label className="text-sm font-medium text-slate-300">CVV</label>
                  <input 
                    type="password" 
                    value={cvv}
                    onChange={(e) => setCvv(e.target.value.replace(/\D/g, '').substring(0, 4))}
                    placeholder="123"
                    className={`w-full bg-slate-950 border ${formErrors.cvv ? 'border-red-500/50' : 'border-slate-800'} rounded-lg px-4 py-3 text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/50 transition-all`}
                  />
                  {formErrors.cvv && <p className="text-xs text-red-400">{formErrors.cvv}</p>}
                </div>
              </div>
            </div>
          )}

          {method === PaymentMethodType.TRANSFER && (
            <div className="p-4 bg-slate-800/50 border border-slate-700 rounded-xl animate-in fade-in">
              <p className="text-sm text-slate-300 text-center">
                Se generarán las instrucciones de transferencia bancaria al confirmar la orden.
              </p>
            </div>
          )}

          <button 
            type="submit" 
            disabled={isPending}
            className="w-full py-4 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-medium transition-all shadow-lg shadow-blue-500/20 disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-4"
          >
            {isPending ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Procesando pago...
              </>
            ) : (
              'Pagar Ahora'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};
