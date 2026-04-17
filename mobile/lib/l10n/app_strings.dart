class AppStrings {
  final String languageName;
  // Auth
  final String welcome;
  final String welcomeSub;
  final String mobileNumber;
  final String sendOtp;
  final String sendingOtp;
  final String enterOtp;
  final String verify;
  final String verifying;
  final String termsPrivacy;
  final String howItWorks;
  final String howItWorksReal;
  final String howItWorksDemo;
  final String serverWakeup;
  final String invalidPhone;
  // Nav
  final String home;
  final String policy;
  final String claims;
  final String risk;
  final String profile;
  // Home
  final String quickActions;
  final String activeDisruptions;
  final String noDisruptions;
  final String buyPolicy;
  final String renewPolicy;
  final String recentClaims;
  final String seeAll;
  final String protectedThisMonth;
  final String claimsFiled;
  // Policy
  final String myPolicy;
  final String noPolicyActive;
  final String noActivePolicy;
  final String protectionDesc;
  final String buyWeeklyPolicy;
  final String coverageDetails;
  final String maxDailyPayout;
  final String maxWeeklyPayout;
  final String totalClaimedThisWeek;
  final String claimsThisWeek;
  final String triggersCovered;
  final String renewChangePlan;
  final String active;
  final String buyNow;
  final String allClear;
  final String simulateEvent;
  final String hello;
  // Claims
  final String claimsHistory;
  final String noClaimsYet;
  final String claimsAutoTriggeredDesc;
  final String claim;
  final String aiAuto;
  final String dss;
  final String fraudScore;
  final String claimed;
  final String pending;
  final String approved;
  final String paid;
  final String rejected;
  // Live Risk
  final String liveRisk;
  final String riskProbability;
  final String riskFactorBreakdown;
  final String personalRiskScore;
  final String activeRiskFactors;
  final String lowRisk;
  final String moderateRisk;
  final String highRisk;
  final String fetchingLiveWeather;
  final String humidity;
  final String wind;
  final String rain;
  final String visibility;
  final String good;
  final String moderate;
  final String poor;
  final String veryPoor;
  // Profile
  final String accountDetails;
  final String riskProfile;
  final String logout;
  final String mobile;
  final String upiId;
  final String city;
  final String avgDailyEarnings;
  final String riskScore;
  final String language;
  final String selectLanguage;
  // Location
  final String allowLocation;
  final String allowLocationDesc;
  final String locationNeeded;
  final String locationNeededDesc;
  final String openSettings;
  final String notNow;
  final String allowLocationBtn;
  final String changeAnytime;
  // Registration
  final String selectPlatform;
  final String selectCity;
  final String yourName;
  final String upiIdHint;
  final String avgEarningsHint;
  final String register;
  final String registering;
  // Terms screen UI
  final String termsAndConditions;
  final String pleaseReadTerms;
  final String scrollToRead;
  final String acceptTermsOfService;
  final String acceptPrivacyPolicy;
  final String acceptDataConsent;
  final String acceptAndContinue;
  final String acceptAllToContinue;
  final String confirmAge;
  final String lastUpdated;

  const AppStrings({
    required this.languageName,
    required this.welcome,
    required this.welcomeSub,
    required this.mobileNumber,
    required this.sendOtp,
    required this.sendingOtp,
    required this.enterOtp,
    required this.verify,
    required this.verifying,
    required this.termsPrivacy,
    required this.howItWorks,
    required this.howItWorksReal,
    required this.howItWorksDemo,
    required this.serverWakeup,
    required this.invalidPhone,
    required this.home,
    required this.policy,
    required this.claims,
    required this.risk,
    required this.profile,
    required this.quickActions,
    required this.activeDisruptions,
    required this.noDisruptions,
    required this.buyPolicy,
    required this.renewPolicy,
    required this.recentClaims,
    required this.seeAll,
    required this.protectedThisMonth,
    required this.claimsFiled,
    required this.myPolicy,
    required this.noPolicyActive,
    required this.noActivePolicy,
    required this.protectionDesc,
    required this.buyWeeklyPolicy,
    required this.coverageDetails,
    required this.maxDailyPayout,
    required this.maxWeeklyPayout,
    required this.totalClaimedThisWeek,
    required this.claimsThisWeek,
    required this.triggersCovered,
    required this.renewChangePlan,
    required this.active,
    required this.buyNow,
    required this.allClear,
    required this.simulateEvent,
    required this.hello,
    required this.claimsHistory,
    required this.noClaimsYet,
    required this.claimsAutoTriggeredDesc,
    required this.claim,
    required this.aiAuto,
    required this.dss,
    required this.fraudScore,
    required this.claimed,
    required this.pending,
    required this.approved,
    required this.paid,
    required this.rejected,
    required this.liveRisk,
    required this.riskProbability,
    required this.riskFactorBreakdown,
    required this.personalRiskScore,
    required this.activeRiskFactors,
    required this.lowRisk,
    required this.moderateRisk,
    required this.highRisk,
    required this.fetchingLiveWeather,
    required this.humidity,
    required this.wind,
    required this.rain,
    required this.visibility,
    required this.good,
    required this.moderate,
    required this.poor,
    required this.veryPoor,
    required this.accountDetails,
    required this.riskProfile,
    required this.logout,
    required this.mobile,
    required this.upiId,
    required this.city,
    required this.avgDailyEarnings,
    required this.riskScore,
    required this.language,
    required this.selectLanguage,
    required this.allowLocation,
    required this.allowLocationDesc,
    required this.locationNeeded,
    required this.locationNeededDesc,
    required this.openSettings,
    required this.notNow,
    required this.allowLocationBtn,
    required this.changeAnytime,
    required this.selectPlatform,
    required this.selectCity,
    required this.yourName,
    required this.upiIdHint,
    required this.avgEarningsHint,
    required this.register,
    required this.registering,
    required this.termsAndConditions,
    required this.pleaseReadTerms,
    required this.scrollToRead,
    required this.acceptTermsOfService,
    required this.acceptPrivacyPolicy,
    required this.acceptDataConsent,
    required this.acceptAndContinue,
    required this.acceptAllToContinue,
    required this.confirmAge,
    required this.lastUpdated,
  });

  static const Map<String, AppStrings> all = {'en': _en, 'ta': _ta, 'hi': _hi};
  static AppStrings of(String code) => all[code] ?? _en;
}

const _en = AppStrings(
  languageName: 'English',
  welcome: 'Welcome to\nSusanoo',
  welcomeSub: '"The Ultimate Defense" for delivery heroes.\nEnter your mobile number to get started.',
  mobileNumber: 'Mobile Number',
  sendOtp: 'Send OTP',
  sendingOtp: 'Sending OTP...',
  enterOtp: 'Enter OTP',
  verify: 'Verify',
  verifying: 'Verifying...',
  termsPrivacy: 'By continuing, you agree to our Terms & Privacy Policy',
  howItWorks: 'How it works',
  howItWorksReal: '• Real users: Enter your registered mobile number to receive a live OTP via phone call.',
  howItWorksDemo: '• Demo / Testing: Use any number and enter OTP 123456 to explore the app in demo mode.',
  serverWakeup: 'Please wait up to 30 seconds\nfor the server to wake up.',
  invalidPhone: 'Enter a valid 10-digit number',
  home: 'Home',
  policy: 'Policy',
  claims: 'Claims',
  risk: 'Risk',
  profile: 'Profile',
  quickActions: 'Quick Actions',
  activeDisruptions: 'Active Disruptions',
  noDisruptions: 'No active disruptions',
  buyPolicy: 'Buy Policy',
  renewPolicy: 'Renew Policy',
  recentClaims: 'Recent Claims',
  seeAll: 'See all',
  protectedThisMonth: 'Protected This Month',
  claimsFiled: 'Claims Filed',
  myPolicy: 'My Policy',
  noPolicyActive: 'No active policy',
  noActivePolicy: 'No Active Policy',
  protectionDesc: 'Get protected from income loss due to rain, heat, pollution & more.',
  buyWeeklyPolicy: 'Buy Weekly Policy',
  coverageDetails: 'Coverage Details',
  maxDailyPayout: 'Max Daily Payout',
  maxWeeklyPayout: 'Max Weekly Payout',
  totalClaimedThisWeek: 'Total Claimed (This week)',
  claimsThisWeek: 'Claims This Week',
  triggersCovered: 'Triggers Covered',
  renewChangePlan: 'Renew / Change Plan',
  active: 'Active',
  buyNow: 'Buy Now',
  allClear: 'All clear in your area!',
  simulateEvent: 'Simulate Event',
  hello: 'Hello',
  claimsHistory: 'Claims History',
  noClaimsYet: 'No claims yet',
  claimsAutoTriggeredDesc: 'Claims are auto-triggered when a\ndisruption event is detected in your area.',
  claim: 'Claim',
  aiAuto: 'AI Auto',
  dss: 'DSS',
  fraudScore: 'Fraud Score',
  claimed: 'Claimed',
  pending: 'Pending',
  approved: 'Approved',
  paid: 'Paid',
  rejected: 'Rejected',
  liveRisk: 'Live Risk',
  riskProbability: 'Risk Probability',
  riskFactorBreakdown: 'Risk Factor Breakdown',
  personalRiskScore: 'Personal Risk Score',
  activeRiskFactors: 'Active Risk Factors',
  lowRisk: 'LOW RISK',
  moderateRisk: 'MODERATE RISK',
  highRisk: 'HIGH RISK',
  fetchingLiveWeather: 'Fetching live weather...',
  humidity: 'Humidity',
  wind: 'Wind',
  rain: 'Rain',
  visibility: 'Visibility',
  good: 'Good',
  moderate: 'Moderate',
  poor: 'Poor',
  veryPoor: 'Very Poor',
  accountDetails: 'Account Details',
  riskProfile: 'Risk Profile',
  logout: 'Logout',
  mobile: 'Mobile',
  upiId: 'UPI ID',
  city: 'City',
  avgDailyEarnings: 'Avg Daily Earnings',
  riskScore: 'Risk Score',
  language: 'Language',
  selectLanguage: 'Select Language',
  allowLocation: 'Allow Location Access',
  allowLocationDesc: 'Susanoo uses your location to detect disruptions in your delivery zone and auto-trigger claims when weather or civic events affect your area.',
  locationNeeded: 'Location Access Needed',
  locationNeededDesc: 'Please enable location in Settings to allow Susanoo to detect disruptions in your delivery zone.',
  openSettings: 'Open Settings',
  notNow: 'Not Now',
  allowLocationBtn: 'Allow Location',
  changeAnytime: 'You can change this anytime in Settings.',
  selectPlatform: 'Select Platform',
  selectCity: 'Select City',
  yourName: 'Your Name',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'Average daily earnings (₹)',
  register: 'Complete Registration',
  registering: 'Registering...',
  termsAndConditions: 'Terms & Conditions',
  pleaseReadTerms: 'Please read and accept all terms before continuing.',
  scrollToRead: 'Scroll down to read all terms',
  acceptTermsOfService: 'I have read and agree to the Terms of Service & Insurance Policy Terms',
  acceptPrivacyPolicy: 'I have read and agree to the Privacy Policy',
  acceptDataConsent: 'I consent to location access and data processing as described above.',
  acceptAndContinue: 'Accept & Continue',
  acceptAllToContinue: 'Accept All Terms to Continue',
  confirmAge: 'By continuing, you confirm you are 18+ and an active gig worker.',
  lastUpdated: 'Last updated: April 2025 • Version 1.0',
);

const _ta = AppStrings(
  languageName: 'தமிழ்',
  welcome: 'சுசானூவிற்கு\nவரவேற்கிறோம்',
  welcomeSub: 'டெலிவரி ஹீரோக்களுக்கான "இறுதி பாதுகாப்பு".\nதொடங்க உங்கள் மொபைல் எண்ணை உள்ளிடவும்.',
  mobileNumber: 'மொபைல் எண்',
  sendOtp: 'OTP அனுப்பு',
  sendingOtp: 'OTP அனுப்புகிறது...',
  enterOtp: 'OTP உள்ளிடவும்',
  verify: 'சரிபார்',
  verifying: 'சரிபார்க்கிறது...',
  termsPrivacy: 'தொடர்வதன் மூலம், எங்கள் விதிமுறைகள் & தனியுரிமைக் கொள்கையை ஒப்புக்கொள்கிறீர்கள்',
  howItWorks: 'எப்படி செயல்படுகிறது',
  howItWorksReal: '• உண்மையான பயனர்கள்: OTP தொலைபேசி அழைப்பு மூலம் பெற உங்கள் பதிவு செய்யப்பட்ட மொபைல் எண்ணை உள்ளிடவும்.',
  howItWorksDemo: '• டெமோ / சோதனை: எந்த எண்ணையும் பயன்படுத்தி OTP 123456 உள்ளிட்டு டெமோ பயன்முறையை ஆராயவும்.',
  serverWakeup: 'சர்வர் விழிப்படைய\n30 வினாடிகள் வரை காத்திருக்கவும்.',
  invalidPhone: 'சரியான 10 இலக்க எண்ணை உள்ளிடவும்',
  home: 'முகப்பு',
  policy: 'பாலிசி',
  claims: 'கோரிக்கைகள்',
  risk: 'ரிஸ்க்',
  profile: 'சுயவிவரம்',
  quickActions: 'விரைவு செயல்கள்',
  activeDisruptions: 'செயலில் உள்ள இடையூறுகள்',
  noDisruptions: 'இடையூறுகள் இல்லை',
  buyPolicy: 'பாலிசி வாங்கு',
  renewPolicy: 'பாலிசி புதுப்பி',
  recentClaims: 'சமீபத்திய கோரிக்கைகள்',
  seeAll: 'அனைத்தும் காண்க',
  protectedThisMonth: 'இம்மாதம் பாதுகாக்கப்பட்டது',
  claimsFiled: 'கோரிக்கைகள் தாக்கல்',
  myPolicy: 'என் பாலிசி',
  noPolicyActive: 'செயலில் உள்ள பாலிசி இல்லை',
  noActivePolicy: 'செயலில் உள்ள பாலிசி இல்லை',
  protectionDesc: 'மழை, வெப்பம், மாசு மற்றும் பலவற்றால் வருமான இழப்பிலிருந்து பாதுகாப்பு பெறுங்கள்.',
  buyWeeklyPolicy: 'வாராந்திர பாலிசி வாங்கு',
  coverageDetails: 'கவரேஜ் விவரங்கள்',
  maxDailyPayout: 'அதிகபட்ச தினசரி பணம்',
  maxWeeklyPayout: 'அதிகபட்ச வாராந்திர பணம்',
  totalClaimedThisWeek: 'இந்த வாரம் மொத்த கோரிக்கை',
  claimsThisWeek: 'இந்த வாரம் கோரிக்கைகள்',
  triggersCovered: 'உள்ளடக்கிய தூண்டுதல்கள்',
  renewChangePlan: 'புதுப்பி / திட்டம் மாற்று',
  active: 'செயலில்',
  buyNow: 'இப்போது வாங்கு',
  allClear: 'உங்கள் பகுதியில் அனைத்தும் தெளிவாக உள்ளது!',
  simulateEvent: 'எடுத்துக்காட்டு செய்',
  hello: 'வணக்கம்',
  claimsHistory: 'கோரிக்கை வரலாறு',
  noClaimsYet: 'இன்னும் கோரிக்கைகள் இல்லை',
  claimsAutoTriggeredDesc: 'உங்கள் பகுதியில் இடையூறு கண்டறியப்படும்போது\nகோரிக்கைகள் தானாக தொடங்கப்படும்.',
  claim: 'கோரிக்கை',
  aiAuto: 'AI தானியங்கி',
  dss: 'DSS',
  fraudScore: 'மோசடி மதிப்பெண்',
  claimed: 'கோரப்பட்டது',
  pending: 'நிலுவையில்',
  approved: 'அங்கீகரிக்கப்பட்டது',
  paid: 'செலுத்தப்பட்டது',
  rejected: 'நிராகரிக்கப்பட்டது',
  liveRisk: 'நேரடி ரிஸ்க்',
  riskProbability: 'ரிஸ்க் நிகழ்தகவு',
  riskFactorBreakdown: 'ரிஸ்க் காரணி விவரம்',
  personalRiskScore: 'தனிப்பட்ட ரிஸ்க் மதிப்பெண்',
  activeRiskFactors: 'செயலில் உள்ள ரிஸ்க் காரணிகள்',
  lowRisk: 'குறைந்த ரிஸ்க்',
  moderateRisk: 'மிதமான ரிஸ்க்',
  highRisk: 'அதிக ரிஸ்க்',
  fetchingLiveWeather: 'நேரடி வானிலை பெறுகிறது...',
  humidity: 'ஈரப்பதம்',
  wind: 'காற்று',
  rain: 'மழை',
  visibility: 'தெரிவுத்திறன்',
  good: 'நல்லது',
  moderate: 'மிதமான',
  poor: 'மோசம்',
  veryPoor: 'மிகவும் மோசம்',
  accountDetails: 'கணக்கு விவரங்கள்',
  riskProfile: 'ரிஸ்க் சுயவிவரம்',
  logout: 'வெளியேறு',
  mobile: 'மொபைல்',
  upiId: 'UPI ஐடி',
  city: 'நகரம்',
  avgDailyEarnings: 'சராசரி தினசரி வருமானம்',
  riskScore: 'ரிஸ்க் மதிப்பெண்',
  language: 'மொழி',
  selectLanguage: 'மொழியை தேர்ந்தெடுக்கவும்',
  allowLocation: 'இருப்பிட அணுகலை அனுமதிக்கவும்',
  allowLocationDesc: 'உங்கள் டெலிவரி மண்டலத்தில் இடையூறுகளை கண்டறிய சுசானூ உங்கள் இருப்பிடத்தை பயன்படுத்துகிறது.',
  locationNeeded: 'இருப்பிட அணுகல் தேவை',
  locationNeededDesc: 'சுசானூ உங்கள் டெலிவரி மண்டலத்தில் இடையூறுகளை கண்டறிய அமைப்புகளில் இருப்பிடத்தை இயக்கவும்.',
  openSettings: 'அமைப்புகளை திற',
  notNow: 'இப்போது வேண்டாம்',
  allowLocationBtn: 'இருப்பிடத்தை அனுமதி',
  changeAnytime: 'இதை எப்போது வேண்டுமானாலும் அமைப்புகளில் மாற்றலாம்.',
  selectPlatform: 'தளத்தை தேர்ந்தெடுக்கவும்',
  selectCity: 'நகரத்தை தேர்ந்தெடுக்கவும்',
  yourName: 'உங்கள் பெயர்',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'சராசரி தினசரி வருமானம் (₹)',
  register: 'பதிவை முடிக்கவும்',
  registering: 'பதிவு செய்கிறது...',
  termsAndConditions: 'விதிமுறைகள் & நிபந்தனைகள்',
  pleaseReadTerms: 'தொடர்வதற்கு முன் அனைத்து விதிமுறைகளையும் படித்து ஒப்புக்கொள்ளவும்.',
  scrollToRead: 'அனைத்து விதிமுறைகளையும் படிக்க கீழே உருட்டவும்',
  acceptTermsOfService: 'சேவை விதிமுறைகள் & காப்பீட்டு கொள்கை விதிமுறைகளை படித்து ஒப்புக்கொள்கிறேன்',
  acceptPrivacyPolicy: 'தனியுரிமைக் கொள்கையை படித்து ஒப்புக்கொள்கிறேன்',
  acceptDataConsent: 'மேலே விவரிக்கப்பட்டபடி இருப்பிட அணுகல் மற்றும் தரவு செயலாக்கத்திற்கு சம்மதிக்கிறேன்.',
  acceptAndContinue: 'ஒப்புக்கொண்டு தொடரவும்',
  acceptAllToContinue: 'தொடர அனைத்து விதிமுறைகளையும் ஒப்புக்கொள்ளவும்',
  confirmAge: 'தொடர்வதன் மூலம், நீங்கள் 18+ மற்றும் செயலில் உள்ள கிக் தொழிலாளி என்று உறுதிப்படுத்துகிறீர்கள்.',
  lastUpdated: 'கடைசியாக புதுப்பிக்கப்பட்டது: ஏப்ரல் 2025 • பதிப்பு 1.0',
);

const _hi = AppStrings(
  languageName: 'हिंदी',
  welcome: 'सुसानू में\nआपका स्वागत है',
  welcomeSub: 'डिलीवरी हीरोज़ के लिए "अंतिम सुरक्षा".\nशुरू करने के लिए अपना मोबाइल नंबर दर्ज करें।',
  mobileNumber: 'मोबाइल नंबर',
  sendOtp: 'OTP भेजें',
  sendingOtp: 'OTP भेजा जा रहा है...',
  enterOtp: 'OTP दर्ज करें',
  verify: 'सत्यापित करें',
  verifying: 'सत्यापित हो रहा है...',
  termsPrivacy: 'जारी रखकर, आप हमारी शर्तें और गोपनीयता नीति से सहमत हैं',
  howItWorks: 'यह कैसे काम करता है',
  howItWorksReal: '• वास्तविक उपयोगकर्ता: फ़ोन कॉल के माध्यम से लाइव OTP प्राप्त करने के लिए अपना पंजीकृत मोबाइल नंबर दर्ज करें।',
  howItWorksDemo: '• डेमो / परीक्षण: कोई भी नंबर उपयोग करें और डेमो मोड में ऐप देखने के लिए OTP 123456 दर्ज करें।',
  serverWakeup: 'सर्वर के जागने के लिए\n30 सेकंड तक प्रतीक्षा करें।',
  invalidPhone: 'वैध 10 अंकों का नंबर दर्ज करें',
  home: 'होम',
  policy: 'पॉलिसी',
  claims: 'दावे',
  risk: 'जोखिम',
  profile: 'प्रोफ़ाइल',
  quickActions: 'त्वरित क्रियाएं',
  activeDisruptions: 'सक्रिय व्यवधान',
  noDisruptions: 'कोई व्यवधान नहीं',
  buyPolicy: 'पॉलिसी खरीदें',
  renewPolicy: 'पॉलिसी नवीनीकरण',
  recentClaims: 'हाल के दावे',
  seeAll: 'सभी देखें',
  protectedThisMonth: 'इस महीने सुरक्षित',
  claimsFiled: 'दावे दर्ज',
  myPolicy: 'मेरी पॉलिसी',
  noPolicyActive: 'कोई सक्रिय पॉलिसी नहीं',
  noActivePolicy: 'कोई सक्रिय पॉलिसी नहीं',
  protectionDesc: 'बारिश, गर्मी, प्रदूषण और अधिक से आय हानि से सुरक्षा पाएं।',
  buyWeeklyPolicy: 'साप्ताहिक पॉलिसी खरीदें',
  coverageDetails: 'कवरेज विवरण',
  maxDailyPayout: 'अधिकतम दैनिक भुगतान',
  maxWeeklyPayout: 'अधिकतम साप्ताहिक भुगतान',
  totalClaimedThisWeek: 'इस सप्ताह कुल दावा',
  claimsThisWeek: 'इस सप्ताह दावे',
  triggersCovered: 'कवर किए गए ट्रिगर',
  renewChangePlan: 'नवीनीकरण / योजना बदलें',
  active: 'सक्रिय',
  buyNow: 'अभी खरीदें',
  allClear: 'आपके क्षेत्र में सब साफ है!',
  simulateEvent: 'घटना सिमुलेट करें',
  hello: 'नमस्ते',
  claimsHistory: 'दावों का इतिहास',
  noClaimsYet: 'अभी तक कोई दावा नहीं',
  claimsAutoTriggeredDesc: 'आपके क्षेत्र में व्यवधान का पता चलने पर\nदावे स्वचालित रूप से शुरू होते हैं।',
  claim: 'दावा',
  aiAuto: 'AI स्वतः',
  dss: 'DSS',
  fraudScore: 'धोखाधड़ी स्कोर',
  claimed: 'दावा किया',
  pending: 'लंबित',
  approved: 'स्वीकृत',
  paid: 'भुगतान किया',
  rejected: 'अस्वीकृत',
  liveRisk: 'लाइव जोखिम',
  riskProbability: 'जोखिम संभावना',
  riskFactorBreakdown: 'जोखिम कारक विवरण',
  personalRiskScore: 'व्यक्तिगत जोखिम स्कोर',
  activeRiskFactors: 'सक्रिय जोखिम कारक',
  lowRisk: 'कम जोखिम',
  moderateRisk: 'मध्यम जोखिम',
  highRisk: 'उच्च जोखिम',
  fetchingLiveWeather: 'लाइव मौसम प्राप्त हो रहा है...',
  humidity: 'आर्द्रता',
  wind: 'हवा',
  rain: 'बारिश',
  visibility: 'दृश्यता',
  good: 'अच्छा',
  moderate: 'मध्यम',
  poor: 'खराब',
  veryPoor: 'बहुत खराब',
  accountDetails: 'खाता विवरण',
  riskProfile: 'जोखिम प्रोफ़ाइल',
  logout: 'लॉग आउट',
  mobile: 'मोबाइल',
  upiId: 'UPI आईडी',
  city: 'शहर',
  avgDailyEarnings: 'औसत दैनिक आय',
  riskScore: 'जोखिम स्कोर',
  language: 'भाषा',
  selectLanguage: 'भाषा चुनें',
  allowLocation: 'स्थान पहुँच की अनुमति दें',
  allowLocationDesc: 'सुसानू आपके डिलीवरी क्षेत्र में व्यवधानों का पता लगाने के लिए आपके स्थान का उपयोग करता है।',
  locationNeeded: 'स्थान पहुँच आवश्यक है',
  locationNeededDesc: 'सुसानू को आपके डिलीवरी क्षेत्र में व्यवधानों का पता लगाने के लिए सेटिंग्स में स्थान सक्षम करें।',
  openSettings: 'सेटिंग्स खोलें',
  notNow: 'अभी नहीं',
  allowLocationBtn: 'स्थान की अनुमति दें',
  changeAnytime: 'आप इसे कभी भी सेटिंग्स में बदल सकते हैं।',
  selectPlatform: 'प्लेटफ़ॉर्म चुनें',
  selectCity: 'शहर चुनें',
  yourName: 'आपका नाम',
  upiIdHint: 'yourname@upi',
  avgEarningsHint: 'औसत दैनिक आय (₹)',
  register: 'पंजीकरण पूरा करें',
  registering: 'पंजीकरण हो रहा है...',
  termsAndConditions: 'नियम और शर्तें',
  pleaseReadTerms: 'जारी रखने से पहले सभी शर्तों को पढ़ें और स्वीकार करें.',
  scrollToRead: 'सभी शर्तें पढ़ने के लिए नीचे स्क्रोल करें',
  acceptTermsOfService: 'मैंने सेवा शर्तें और बीमा पॉलिसी शर्तें पढ़ी हैं और सहमत हूं',
  acceptPrivacyPolicy: 'मैंने गोपनीयता नीति पढ़ी है और सहमत हूं',
  acceptDataConsent: 'मैं उपरोक्त विवरण अनुसार स्थान पहुंच और डेटा प्रसंस्करण के लिए सहमति देता हूं.',
  acceptAndContinue: 'स्वीकार करें और जारी रखें',
  acceptAllToContinue: 'जारी रखने के लिए सभी शर्तें स्वीकार करें',
  confirmAge: 'जारी रखकर, आप पुष्टि करते हैं कि आप 18+ हैं और एक सक्रिय गिग वर्कर हैं.',
  lastUpdated: 'अंतिम अपडेट: अप्रैल 2025 • संस्करण 1.0',
);
