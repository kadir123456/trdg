import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

const resources = {
  en: {
    translation: {
      // Auth
      login: "Login",
      register: "Register",
      logout: "Logout",
      name: "Name",
      email: "Email",
      password: "Password",
      enterName: "Enter your name",
      enterEmail: "Enter your email",
      enterPassword: "Enter your password",
      processing: "Processing...",
      needAccount: "Don't have an account? Sign up",
      haveAccount: "Already have an account? Login",
      
      // Dashboard
      welcome: "Welcome",
      dashboardDescription: "Monitor real-time market data and manage your EMA9-EMA21 trading bot strategy.",
      liveMarketData: "Live Market Data",
      
      // Bot Control
      botControl: "Bot Control Panel",
      tradingPair: "Trading Pair",
      timeframe: "Timeframe",
      leverage: "Leverage",
      takeProfit: "Take Profit",
      stopLoss: "Stop Loss",
      positionSize: "Position Size",
      saveConfig: "Save Configuration",
      startBot: "Start Bot",
      stopBot: "Stop Bot",
      configUpdated: "Configuration updated successfully",
      botStarted: "Bot started successfully",
      botStopped: "Bot stopped successfully",
      
      // Footer
      footerDescription: "Professional EMA9-EMA21 trading bot for Binance Futures.",
      features: "Features",
      realTimeData: "Real-time Data",
      emaStrategy: "EMA Strategy",
      secureTrading: "Secure Trading",
      support: "Support",
      documentation: "Documentation",
      contact: "Contact",
      allRightsReserved: "All rights reserved."
    }
  },
  tr: {
    translation: {
      // Auth
      login: "Giriş",
      register: "Kayıt",
      logout: "Çıkış",
      name: "İsim",
      email: "E-posta",
      password: "Şifre",
      enterName: "İsminizi girin",
      enterEmail: "E-postanızı girin",
      enterPassword: "Şifrenizi girin",
      processing: "İşleniyor...",
      needAccount: "Hesabınız yok mu? Kayıt olun",
      haveAccount: "Zaten hesabınız var mı? Giriş yapın",
      
      // Dashboard
      welcome: "Hoş geldiniz",
      dashboardDescription: "Gerçek zamanlı piyasa verilerini izleyin ve EMA9-EMA21 trading bot stratejinizi yönetin.",
      liveMarketData: "Canlı Piyasa Verileri",
      
      // Bot Control
      botControl: "Bot Kontrol Paneli",
      tradingPair: "İşlem Çifti",
      timeframe: "Zaman Dilimi",
      leverage: "Kaldıraç",
      takeProfit: "Kar Al",
      stopLoss: "Zarar Durdur",
      positionSize: "Pozisyon Büyüklüğü",
      saveConfig: "Yapılandırmayı Kaydet",
      startBot: "Botu Başlat",
      stopBot: "Botu Durdur",
      configUpdated: "Yapılandırma başarıyla güncellendi",
      botStarted: "Bot başarıyla başlatıldı",
      botStopped: "Bot başarıyla durduruldu",
      
      // Footer
      footerDescription: "Binance Futures için profesyonel EMA9-EMA21 trading bot.",
      features: "Özellikler",
      realTimeData: "Gerçek Zamanlı Veri",
      emaStrategy: "EMA Stratejisi",
      secureTrading: "Güvenli İşlem",
      support: "Destek",
      documentation: "Dokümantasyon",
      contact: "İletişim",
      allRightsReserved: "Tüm hakları saklıdır."
    }
  }
};

i18n
  .use(initReactI18next)
  .init({
    resources,
    lng: 'tr', // default language
    fallbackLng: 'en',
    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;