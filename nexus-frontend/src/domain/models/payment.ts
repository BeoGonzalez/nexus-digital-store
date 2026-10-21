export enum PaymentMethodType {
  CREDIT_CARD = 'CREDIT_CARD',
  DEBIT_CARD = 'DEBIT_CARD',
  TRANSFER = 'TRANSFER',
}

export interface PaymentMethod {
  id: string;
  userId: string;
  methodType: PaymentMethodType;
  cardLast4: string;
  cardBrand: string;
  isDefault: boolean;
}

export interface CreatePaymentMethodDTO {
  cardNumber: string;
  cardBrand: string;
  isDefault: boolean;
  methodType: PaymentMethodType;
}
