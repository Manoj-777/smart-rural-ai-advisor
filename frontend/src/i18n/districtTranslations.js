// District name translations for all Indian states
// Organized by language code → { English district name: translated name }
// Covers: Hindi for ALL states, + matching regional language for each state

const DT = {};

// ═══════════════════════════════════════════════════════════════════════
// HINDI (hi-IN) — All states
// ═══════════════════════════════════════════════════════════════════════
DT['hi-IN'] = {
    // Andhra Pradesh
    'Anantapur': 'अनंतपुर', 'Chittoor': 'चित्तूर', 'East Godavari': 'पूर्वी गोदावरी', 'Guntur': 'गुंटूर',
    'Krishna': 'कृष्णा', 'Kurnool': 'कुर्नूल', 'Nellore': 'नेल्लूर', 'Prakasam': 'प्रकाशम',
    'Srikakulam': 'श्रीकाकुलम', 'Visakhapatnam': 'विशाखापट्टनम', 'Vizianagaram': 'विजयनगरम',
    'West Godavari': 'पश्चिमी गोदावरी', 'YSR Kadapa': 'वाईएसआर कडप्पा',
    'Alluri Sitharama Raju': 'अल्लूरि सीतारामराजू', 'Anakapalli': 'अनकापल्ली', 'Bapatla': 'बापट्ला',
    'Eluru': 'एलूरु', 'Kakinada': 'काकीनाडा', 'Konaseema': 'कोनसीमा', 'NTR': 'एनटीआर',
    'Palnadu': 'पल्नाडु', 'Parvathipuram Manyam': 'पार्वतीपुरम मन्यम',
    'Sri Sathya Sai': 'श्री सत्यसाई', 'Tirupati': 'तिरुपति',

    // Arunachal Pradesh
    'Tawang': 'तवांग', 'West Kameng': 'पश्चिमी कामेंग', 'East Kameng': 'पूर्वी कामेंग',
    'Papum Pare': 'पापुम पारे', 'Kurung Kumey': 'कुरुंग कुमे', 'Lower Subansiri': 'निचला सुबनसिरी',
    'Upper Subansiri': 'ऊपरी सुबनसिरी', 'West Siang': 'पश्चिमी सियांग', 'East Siang': 'पूर्वी सियांग',
    'Upper Siang': 'ऊपरी सियांग', 'Changlang': 'चांगलांग', 'Tirap': 'तिरप',
    'Lower Dibang Valley': 'निचला दिबांग घाटी', 'Lohit': 'लोहित', 'Anjaw': 'अंजॉ',
    'Longding': 'लोंगडिंग', 'Namsai': 'नामसई', 'Siang': 'सियांग', 'Kamle': 'कामले',
    'Pakke-Kessang': 'पक्के-केसांग', 'Lepa Rada': 'लेपा राडा', 'Shi Yomi': 'शी योमी',
    'Upper Dibang Valley': 'ऊपरी दिबांग घाटी',

    // Assam
    'Baksa': 'बक्सा', 'Barpeta': 'बारपेटा', 'Bongaigaon': 'बोंगाईगांव', 'Cachar': 'कछार',
    'Chirang': 'चिरांग', 'Darrang': 'दरांग', 'Dhemaji': 'धेमाजी', 'Dhubri': 'धुबरी',
    'Dibrugarh': 'डिब्रूगढ़', 'Dima Hasao': 'डिमा हसाओ', 'Goalpara': 'गोलपारा',
    'Golaghat': 'गोलाघाट', 'Hailakandi': 'हैलाकांदी', 'Jorhat': 'जोरहाट', 'Kamrup': 'कामरूप',
    'Kamrup Metropolitan': 'कामरूप महानगर', 'Karbi Anglong': 'कार्बी आंगलोंग',
    'Karimganj': 'करीमगंज', 'Kokrajhar': 'कोकराझार', 'Lakhimpur': 'लखीमपुर',
    'Morigaon': 'मोरीगांव', 'Nagaon': 'नगांव', 'Nalbari': 'नलबारी', 'Sivasagar': 'शिवसागर',
    'Sonitpur': 'शोणितपुर', 'Tinsukia': 'तिनसुकिया', 'Udalguri': 'उदालगुरी',

    // Bihar
    'Araria': 'अररिया', 'Arwal': 'अरवल', 'Aurangabad': 'औरंगाबाद', 'Banka': 'बांका',
    'Begusarai': 'बेगूसराय', 'Bhagalpur': 'भागलपुर', 'Bhojpur': 'भोजपुर', 'Buxar': 'बक्सर',
    'Darbhanga': 'दरभंगा', 'East Champaran': 'पूर्वी चंपारण', 'Gaya': 'गया',
    'Gopalganj': 'गोपालगंज', 'Jamui': 'जमुई', 'Jehanabad': 'जहानाबाद', 'Kaimur': 'कैमूर',
    'Katihar': 'कटिहार', 'Khagaria': 'खगड़िया', 'Kishanganj': 'किशनगंज',
    'Lakhisarai': 'लखीसराय', 'Madhepura': 'मधेपुरा', 'Madhubani': 'मधुबनी',
    'Munger': 'मुंगेर', 'Muzaffarpur': 'मुजफ्फरपुर', 'Nalanda': 'नालंदा', 'Nawada': 'नवादा',
    'Patna': 'पटना', 'Purnia': 'पूर्णिया', 'Rohtas': 'रोहतास', 'Saharsa': 'सहरसा',
    'Samastipur': 'समस्तीपुर', 'Saran': 'सारण', 'Sheikhpura': 'शेखपुरा', 'Sheohar': 'शिवहर',
    'Sitamarhi': 'सीतामढ़ी', 'Supaul': 'सुपौल', 'Vaishali': 'वैशाली',
    'West Champaran': 'पश्चिमी चंपारण',

    // Chhattisgarh
    'Balod': 'बालोद', 'Baloda Bazar': 'बलौदा बाजार', 'Balrampur': 'बलरामपुर', 'Bastar': 'बस्तर',
    'Bemetara': 'बेमेतरा', 'Bijapur': 'बीजापुर', 'Bilaspur': 'बिलासपुर',
    'Dantewada': 'दंतेवाड़ा', 'Dhamtari': 'धमतरी', 'Durg': 'दुर्ग', 'Gariaband': 'गरियाबंद',
    'Janjgir-Champa': 'जांजगीर-चांपा', 'Jashpur': 'जशपुर', 'Kabirdham': 'कबीरधाम',
    'Kanker': 'कांकेर', 'Kondagaon': 'कोंडागांव', 'Korba': 'कोरबा', 'Koriya': 'कोरिया',
    'Mahasamund': 'महासमुंद', 'Mungeli': 'मुंगेली', 'Narayanpur': 'नारायणपुर',
    'Raigarh': 'रायगढ़', 'Raipur': 'रायपुर', 'Rajnandgaon': 'राजनांदगांव', 'Sukma': 'सुकमा',
    'Surajpur': 'सूरजपुर', 'Surguja': 'सरगुजा',

    // Goa
    'North Goa': 'उत्तर गोवा', 'South Goa': 'दक्षिण गोवा',

    // Gujarat
    'Ahmedabad': 'अहमदाबाद', 'Amreli': 'अमरेली', 'Anand': 'आनंद', 'Aravalli': 'अरावली',
    'Banaskantha': 'बनासकांठा', 'Bharuch': 'भरूच', 'Bhavnagar': 'भावनगर', 'Botad': 'बोटाद',
    'Chhota Udaipur': 'छोटा उदयपुर', 'Dahod': 'दाहोद', 'Dang': 'डांग',
    'Devbhumi Dwarka': 'देवभूमि द्वारका', 'Gandhinagar': 'गांधीनगर',
    'Gir Somnath': 'गिर सोमनाथ', 'Jamnagar': 'जामनगर', 'Junagadh': 'जूनागढ़', 'Kutch': 'कच्छ',
    'Kheda': 'खेड़ा', 'Mahisagar': 'महीसागर', 'Mehsana': 'मेहसाणा', 'Morbi': 'मोरबी',
    'Narmada': 'नर्मदा', 'Navsari': 'नवसारी', 'Panchmahal': 'पंचमहल', 'Patan': 'पाटण',
    'Porbandar': 'पोरबंदर', 'Rajkot': 'राजकोट', 'Sabarkantha': 'साबरकांठा', 'Surat': 'सूरत',
    'Surendranagar': 'सुरेंद्रनगर', 'Tapi': 'तापी', 'Vadodara': 'वडोदरा', 'Valsad': 'वलसाड',

    // Haryana
    'Ambala': 'अंबाला', 'Bhiwani': 'भिवानी', 'Charkhi Dadri': 'चरखी दादरी',
    'Faridabad': 'फरीदाबाद', 'Fatehabad': 'फतेहाबाद', 'Gurugram': 'गुरुग्राम', 'Hisar': 'हिसार',
    'Jhajjar': 'झज्जर', 'Jind': 'जींद', 'Kaithal': 'कैथल', 'Karnal': 'करनाल',
    'Kurukshetra': 'कुरुक्षेत्र', 'Mahendragarh': 'महेंद्रगढ़', 'Nuh': 'नूंह', 'Palwal': 'पलवल',
    'Panchkula': 'पंचकूला', 'Panipat': 'पानीपत', 'Rewari': 'रेवाड़ी', 'Rohtak': 'रोहतक',
    'Sirsa': 'सिरसा', 'Sonipat': 'सोनीपत', 'Yamunanagar': 'यमुनानगर',

    // Himachal Pradesh
    'Chamba': 'चंबा', 'Hamirpur': 'हमीरपुर', 'Kangra': 'कांगड़ा', 'Kinnaur': 'किन्नौर',
    'Kullu': 'कुल्लू', 'Lahaul and Spiti': 'लाहौल और स्पिति', 'Mandi': 'मंडी',
    'Shimla': 'शिमला', 'Sirmaur': 'सिरमौर', 'Solan': 'सोलन', 'Una': 'ऊना',

    // Jharkhand
    'Bokaro': 'बोकारो', 'Chatra': 'चतरा', 'Deoghar': 'देवघर', 'Dhanbad': 'धनबाद',
    'Dumka': 'दुमका', 'East Singhbhum': 'पूर्वी सिंहभूम', 'Garhwa': 'गढ़वा',
    'Giridih': 'गिरिडीह', 'Godda': 'गोड्डा', 'Gumla': 'गुमला', 'Hazaribagh': 'हजारीबाग',
    'Jamtara': 'जामताड़ा', 'Khunti': 'खूंटी', 'Koderma': 'कोडरमा', 'Latehar': 'लातेहार',
    'Lohardaga': 'लोहरदगा', 'Pakur': 'पाकुड़', 'Palamu': 'पलामू', 'Ramgarh': 'रामगढ़',
    'Ranchi': 'रांची', 'Sahibganj': 'साहिबगंज', 'Seraikela Kharsawan': 'सरायकेला खरसावां',
    'Simdega': 'सिमडेगा', 'West Singhbhum': 'पश्चिमी सिंहभूम',

    // Karnataka
    'Bagalkot': 'बागलकोट', 'Bangalore Rural': 'बेंगलूरु ग्रामीण',
    'Bangalore Urban': 'बेंगलूरु शहरी', 'Belgaum': 'बेलगाम', 'Bellary': 'बेल्लारी',
    'Bidar': 'बीदर', 'Chamarajanagar': 'चामराजनगर', 'Chikkaballapur': 'चिक्कबल्लापुर',
    'Chikkamagaluru': 'चिक्कमगलूरु', 'Chitradurga': 'चित्रदुर्ग',
    'Dakshina Kannada': 'दक्षिण कन्नड़', 'Davanagere': 'दावणगेरे', 'Dharwad': 'धारवाड़',
    'Gadag': 'गदग', 'Hassan': 'हासन', 'Haveri': 'हावेरी', 'Kalaburagi': 'कलबुर्गी',
    'Kodagu': 'कोडगु', 'Kolar': 'कोलार', 'Koppal': 'कोप्पल', 'Mandya': 'मंड्या',
    'Mysore': 'मैसूर', 'Raichur': 'रायचूर', 'Ramanagara': 'रामनगर', 'Shimoga': 'शिमोगा',
    'Tumkur': 'तुमकूर', 'Udupi': 'उडुपी', 'Uttara Kannada': 'उत्तर कन्नड़',
    'Vijayapura': 'विजयपुर', 'Yadgir': 'यादगीर',

    // Kerala
    'Alappuzha': 'आलप्पुझा', 'Ernakulam': 'एर्णाकुलम', 'Idukki': 'इडुक्की', 'Kannur': 'कन्नूर',
    'Kasaragod': 'कासरगोड', 'Kollam': 'कोल्लम', 'Kottayam': 'कोट्टयम',
    'Kozhikode': 'कोझिकोड', 'Malappuram': 'मलप्पुरम', 'Palakkad': 'पालक्काड',
    'Pathanamthitta': 'पतनमथिट्टा', 'Thiruvananthapuram': 'तिरुवनंतपुरम',
    'Thrissur': 'त्रिशूर', 'Wayanad': 'वायनाड',

    // Madhya Pradesh
    'Agar Malwa': 'आगर मालवा', 'Alirajpur': 'अलीराजपुर', 'Anuppur': 'अनूपपुर',
    'Ashoknagar': 'अशोकनगर', 'Balaghat': 'बालाघाट', 'Barwani': 'बड़वानी', 'Betul': 'बैतूल',
    'Bhind': 'भिंड', 'Bhopal': 'भोपाल', 'Burhanpur': 'बुरहानपुर', 'Chhatarpur': 'छतरपुर',
    'Chhindwara': 'छिंदवाड़ा', 'Damoh': 'दमोह', 'Datia': 'दतिया', 'Dewas': 'देवास',
    'Dhar': 'धार', 'Dindori': 'डिंडोरी', 'Guna': 'गुना', 'Gwalior': 'ग्वालियर',
    'Harda': 'हरदा', 'Hoshangabad': 'होशंगाबाद', 'Indore': 'इंदौर', 'Jabalpur': 'जबलपुर',
    'Jhabua': 'झाबुआ', 'Katni': 'कटनी', 'Khandwa': 'खंडवा', 'Khargone': 'खरगोन',
    'Mandla': 'मंडला', 'Mandsaur': 'मंदसौर', 'Morena': 'मुरैना', 'Narsinghpur': 'नरसिंहपुर',
    'Neemuch': 'नीमच', 'Panna': 'पन्ना', 'Raisen': 'रायसेन', 'Rajgarh': 'राजगढ़',
    'Ratlam': 'रतलाम', 'Rewa': 'रीवा', 'Sagar': 'सागर', 'Satna': 'सतना', 'Sehore': 'सीहोर',
    'Seoni': 'सिवनी', 'Shahdol': 'शहडोल', 'Shajapur': 'शाजापुर', 'Sheopur': 'श्योपुर',
    'Shivpuri': 'शिवपुरी', 'Sidhi': 'सीधी', 'Singrauli': 'सिंगरौली', 'Tikamgarh': 'टीकमगढ़',
    'Ujjain': 'उज्जैन', 'Umaria': 'उमरिया', 'Vidisha': 'विदिशा',

    // Maharashtra
    'Ahmednagar': 'अहमदनगर', 'Akola': 'अकोला', 'Amravati': 'अमरावती', 'Beed': 'बीड',
    'Bhandara': 'भंडारा', 'Buldhana': 'बुलढाणा', 'Chandrapur': 'चंद्रपुर', 'Dhule': 'धुळे',
    'Gadchiroli': 'गडचिरोली', 'Gondia': 'गोंदिया', 'Hingoli': 'हिंगोली', 'Jalgaon': 'जळगांव',
    'Jalna': 'जालना', 'Kolhapur': 'कोल्हापुर', 'Latur': 'लातूर', 'Mumbai City': 'मुंबई शहर',
    'Mumbai Suburban': 'मुंबई उपनगर', 'Nagpur': 'नागपुर', 'Nanded': 'नांदेड',
    'Nandurbar': 'नंदुरबार', 'Nashik': 'नासिक', 'Osmanabad': 'उस्मानाबाद',
    'Palghar': 'पालघर', 'Parbhani': 'परभणी', 'Pune': 'पुणे', 'Raigad': 'रायगड',
    'Ratnagiri': 'रत्नागिरी', 'Sangli': 'सांगली', 'Satara': 'सातारा',
    'Sindhudurg': 'सिंधुदुर्ग', 'Solapur': 'सोलापुर', 'Thane': 'ठाणे', 'Wardha': 'वर्धा',
    'Washim': 'वाशिम', 'Yavatmal': 'यवतमाल',

    // Manipur
    'Bishnupur': 'बिष्णुपुर', 'Chandel': 'चंदेल', 'Churachandpur': 'चुराचांदपुर',
    'Imphal East': 'इम्फाल पूर्वी', 'Imphal West': 'इम्फाल पश्चिमी', 'Jiribam': 'जीरीबाम',
    'Kakching': 'काकचिंग', 'Kamjong': 'कामजोंग', 'Kangpokpi': 'कांगपोकपी', 'Noney': 'नोनी',
    'Pherzawl': 'फेरजोल', 'Senapati': 'सेनापति', 'Tamenglong': 'तामेंगलोंग',
    'Tengnoupal': 'तेंग्नूपाल', 'Thoubal': 'थौबल', 'Ukhrul': 'उखरूल',

    // Meghalaya
    'East Garo Hills': 'पूर्वी गारो हिल्स', 'East Jaintia Hills': 'पूर्वी जयंतिया हिल्स',
    'East Khasi Hills': 'पूर्वी खासी हिल्स', 'North Garo Hills': 'उत्तरी गारो हिल्स',
    'Ri Bhoi': 'री भोई', 'South Garo Hills': 'दक्षिणी गारो हिल्स',
    'South West Garo Hills': 'दक्षिण पश्चिम गारो हिल्स',
    'South West Khasi Hills': 'दक्षिण पश्चिम खासी हिल्स',
    'West Garo Hills': 'पश्चिमी गारो हिल्स', 'West Jaintia Hills': 'पश्चिमी जयंतिया हिल्स',
    'West Khasi Hills': 'पश्चिमी खासी हिल्स',

    // Mizoram
    'Aizawl': 'आइजोल', 'Champhai': 'चम्फाई', 'Hnahthial': 'नाहथियाल', 'Khawzawl': 'खॉजोल',
    'Kolasib': 'कोलासिब', 'Lawngtlai': 'लॉन्गट्लाई', 'Lunglei': 'लुंगलेई', 'Mamit': 'मामित',
    'Saiha': 'सैहा', 'Saitual': 'सैतुअल', 'Serchhip': 'सेरछिप',

    // Nagaland
    'Chumukedima': 'चुमुकेदीमा', 'Dimapur': 'दीमापुर', 'Kiphire': 'किफिरे', 'Kohima': 'कोहिमा',
    'Longleng': 'लोंगलेंग', 'Mokokchung': 'मोकोकचुंग', 'Mon': 'मोन', 'Noklak': 'नोक्लक',
    'Peren': 'पेरेन', 'Phek': 'फेक', 'Shamator': 'शामाटोर', 'Tseminyu': 'त्सेमिन्यू',
    'Tuensang': 'तुएनसांग', 'Wokha': 'वोखा', 'Zunheboto': 'ज़ुन्हेबोटो',

    // Odisha
    'Angul': 'अंगुल', 'Balangir': 'बलांगीर', 'Balasore': 'बालासोर', 'Bargarh': 'बरगढ़',
    'Bhadrak': 'भद्रक', 'Boudh': 'बौध', 'Cuttack': 'कटक', 'Deogarh': 'देवगढ़',
    'Dhenkanal': 'ढेंकनाल', 'Gajapati': 'गजपति', 'Ganjam': 'गंजाम',
    'Jagatsinghpur': 'जगतसिंहपुर', 'Jajpur': 'जाजपुर', 'Jharsuguda': 'झारसुगुड़ा',
    'Kalahandi': 'कालाहांडी', 'Kandhamal': 'कंधमाल', 'Kendrapara': 'केंद्रापाड़ा',
    'Kendujhar': 'केंदुझर', 'Khordha': 'खोरधा', 'Koraput': 'कोरापुट',
    'Malkangiri': 'मालकानगिरी', 'Mayurbhanj': 'मयूरभंज', 'Nabarangpur': 'नबरंगपुर',
    'Nayagarh': 'नयागढ़', 'Nuapada': 'नुआपाड़ा', 'Puri': 'पुरी', 'Rayagada': 'रायगड़ा',
    'Sambalpur': 'संबलपुर', 'Subarnapur': 'सुबर्णपुर', 'Sundargarh': 'सुंदरगढ़',

    // Puducherry
    'Puducherry': 'पुदुच्चेरी', 'Karaikal': 'कराइकल', 'Mahe': 'माहे', 'Yanam': 'यानम',

    // Punjab
    'Amritsar': 'अमृतसर', 'Barnala': 'बरनाला', 'Bathinda': 'बठिंडा', 'Faridkot': 'फरीदकोट',
    'Fatehgarh Sahib': 'फतेहगढ़ साहिब', 'Fazilka': 'फाजिल्का', 'Ferozepur': 'फिरोजपुर',
    'Gurdaspur': 'गुरदासपुर', 'Hoshiarpur': 'होशियारपुर', 'Jalandhar': 'जालंधर',
    'Kapurthala': 'कपूरथला', 'Ludhiana': 'लुधियाना', 'Malerkotla': 'मलेरकोटला',
    'Mansa': 'मानसा', 'Moga': 'मोगा', 'Mohali': 'मोहाली', 'Muktsar': 'मुक्तसर',
    'Pathankot': 'पठानकोट', 'Patiala': 'पटियाला', 'Rupnagar': 'रूपनगर', 'Sangrur': 'संगरूर',
    'Shaheed Bhagat Singh Nagar': 'शहीद भगत सिंह नगर', 'Tarn Taran': 'तरन तारन',

    // Rajasthan
    'Ajmer': 'अजमेर', 'Alwar': 'अलवर', 'Banswara': 'बांसवाड़ा', 'Baran': 'बारां',
    'Barmer': 'बाड़मेर', 'Bharatpur': 'भरतपुर', 'Bhilwara': 'भीलवाड़ा', 'Bikaner': 'बीकानेर',
    'Bundi': 'बूंदी', 'Chittorgarh': 'चित्तौड़गढ़', 'Churu': 'चूरू', 'Dausa': 'दौसा',
    'Dholpur': 'धौलपुर', 'Dungarpur': 'डूंगरपुर', 'Hanumangarh': 'हनुमानगढ़',
    'Jaipur': 'जयपुर', 'Jaisalmer': 'जैसलमेर', 'Jalore': 'जालोर', 'Jhalawar': 'झालावाड़',
    'Jhunjhunu': 'झुंझुनूं', 'Jodhpur': 'जोधपुर', 'Karauli': 'करौली', 'Kota': 'कोटा',
    'Nagaur': 'नागौर', 'Pali': 'पाली', 'Pratapgarh': 'प्रतापगढ़', 'Rajsamand': 'राजसमंद',
    'Sawai Madhopur': 'सवाई माधोपुर', 'Sikar': 'सीकर', 'Sirohi': 'सिरोही',
    'Sri Ganganagar': 'श्री गंगानगर', 'Tonk': 'टोंक', 'Udaipur': 'उदयपुर',

    // Sikkim
    'East Sikkim': 'पूर्वी सिक्किम', 'North Sikkim': 'उत्तर सिक्किम',
    'South Sikkim': 'दक्षिण सिक्किम', 'West Sikkim': 'पश्चिम सिक्किम',
    'Pakyong': 'पाक्योंग', 'Soreng': 'सोरेंग',

    // Tamil Nadu
    'Ariyalur': 'अरियालूर', 'Chengalpattu': 'चेंगलपट्टू', 'Chennai': 'चेन्नई',
    'Coimbatore': 'कोयंबत्तूर', 'Cuddalore': 'कडलूर', 'Dharmapuri': 'धर्मपुरी',
    'Dindigul': 'डिंडिगुल', 'Erode': 'ईरोड', 'Kallakurichi': 'कल्लकुरिची',
    'Kancheepuram': 'कांचीपुरम', 'Karur': 'करूर', 'Krishnagiri': 'कृष्णगिरि',
    'Madurai': 'मदुरई', 'Mayiladuthurai': 'मयिलाडुतुरै', 'Nagapattinam': 'नागपट्टिनम',
    'Namakkal': 'नामक्कल', 'Nilgiris': 'नीलगिरी', 'Perambalur': 'पेरंबलूर',
    'Pudukkottai': 'पुदुक्कोट्टई', 'Ramanathapuram': 'रामनाथपुरम', 'Ranipet': 'रानीपेट',
    'Salem': 'सेलम', 'Sivaganga': 'शिवगंगा', 'Tenkasi': 'तेनकासी', 'Thanjavur': 'तंजावूर',
    'Theni': 'तेनी', 'Thoothukudi': 'तूतीकोरिन', 'Tiruchirappalli': 'तिरुचिरापल्ली',
    'Tirunelveli': 'तिरुनेलवेली', 'Tirupathur': 'तिरुपत्तूर', 'Tiruppur': 'तिरुप्पूर',
    'Tiruvallur': 'तिरुवल्लूर', 'Tiruvannamalai': 'तिरुवन्नामलै',
    'Tiruvarur': 'तिरुवारूर', 'Vellore': 'वेल्लूर', 'Viluppuram': 'विलुप्पुरम',
    'Virudhunagar': 'विरुधुनगर',

    // Telangana
    'Adilabad': 'आदिलाबाद', 'Bhadradri Kothagudem': 'भद्राद्रि कोठागुडेम',
    'Hyderabad': 'हैदराबाद', 'Jagtial': 'जगतियाल', 'Jangaon': 'जनगांव',
    'Jayashankar Bhupalpally': 'जयशंकर भूपालपल्ली', 'Jogulamba Gadwal': 'जोगुलांबा गद्वाल',
    'Kamareddy': 'कामारेड्डी', 'Karimnagar': 'करीमनगर', 'Khammam': 'खम्मम',
    'Komaram Bheem': 'कोमराम भीम', 'Mahabubabad': 'महबूबाबाद', 'Mahbubnagar': 'महबूबनगर',
    'Mancherial': 'मंचीर्याल', 'Medak': 'मेदक', 'Medchal-Malkajgiri': 'मेडचल-मल्काजगिरी',
    'Mulugu': 'मुलुगु', 'Nagarkurnool': 'नागरकुर्नूल', 'Nalgonda': 'नलगोंडा',
    'Narayanpet': 'नारायणपेट', 'Nirmal': 'निर्मल', 'Nizamabad': 'निजामाबाद',
    'Peddapalli': 'पेद्दापल्ली', 'Rajanna Sircilla': 'राजन्ना सिरसिल्ला',
    'Rangareddy': 'रंगारेड्डी', 'Sangareddy': 'संगारेड्डी', 'Siddipet': 'सिद्दीपेट',
    'Suryapet': 'सूर्यापेट', 'Vikarabad': 'विकाराबाद', 'Wanaparthy': 'वनपर्ती',
    'Warangal Rural': 'वारंगल ग्रामीण', 'Warangal Urban': 'वारंगल शहरी',
    'Yadadri Bhuvanagiri': 'यादाद्रि भुवनगिरि',

    // Tripura
    'Dhalai': 'धलाई', 'Gomati': 'गोमती', 'Khowai': 'खोवाई',
    'North Tripura': 'उत्तर त्रिपुरा', 'Sepahijala': 'सिपाहीजला',
    'South Tripura': 'दक्षिण त्रिपुरा', 'Unakoti': 'उनकोटी', 'West Tripura': 'पश्चिम त्रिपुरा',

    // Uttar Pradesh
    'Agra': 'आगरा', 'Aligarh': 'अलीगढ़', 'Ambedkar Nagar': 'अंबेडकर नगर', 'Amethi': 'अमेठी',
    'Amroha': 'अमरोहा', 'Auraiya': 'औरैया', 'Ayodhya': 'अयोध्या', 'Azamgarh': 'आजमगढ़',
    'Baghpat': 'बागपत', 'Bahraich': 'बहराइच', 'Ballia': 'बलिया', 'Banda': 'बांदा',
    'Barabanki': 'बाराबंकी', 'Bareilly': 'बरेली', 'Basti': 'बस्ती', 'Bhadohi': 'भदोही',
    'Bijnor': 'बिजनौर', 'Budaun': 'बदायूं', 'Bulandshahr': 'बुलंदशहर',
    'Chandauli': 'चंदौली', 'Chitrakoot': 'चित्रकूट', 'Deoria': 'देवरिया', 'Etah': 'एटा',
    'Etawah': 'इटावा', 'Farrukhabad': 'फर्रुखाबाद', 'Fatehpur': 'फतेहपुर',
    'Firozabad': 'फिरोजाबाद', 'Gautam Buddha Nagar': 'गौतमबुद्ध नगर',
    'Ghaziabad': 'गाजियाबाद', 'Ghazipur': 'गाजीपुर', 'Gonda': 'गोंडा',
    'Gorakhpur': 'गोरखपुर', 'Hapur': 'हापुड़', 'Hardoi': 'हरदोई', 'Hathras': 'हाथरस',
    'Jalaun': 'जालौन', 'Jaunpur': 'जौनपुर', 'Jhansi': 'झांसी', 'Kannauj': 'कन्नौज',
    'Kanpur Dehat': 'कानपुर देहात', 'Kanpur Nagar': 'कानपुर नगर', 'Kasganj': 'कासगंज',
    'Kaushambi': 'कौशांबी', 'Kushinagar': 'कुशीनगर', 'Lakhimpur Kheri': 'लखीमपुर खीरी',
    'Lalitpur': 'ललितपुर', 'Lucknow': 'लखनऊ', 'Maharajganj': 'महाराजगंज', 'Mahoba': 'महोबा',
    'Mainpuri': 'मैनपुरी', 'Mathura': 'मथुरा', 'Mau': 'मऊ', 'Meerut': 'मेरठ',
    'Mirzapur': 'मिर्जापुर', 'Moradabad': 'मुरादाबाद', 'Muzaffarnagar': 'मुजफ्फरनगर',
    'Pilibhit': 'पीलीभीत', 'Prayagraj': 'प्रयागराज', 'Rae Bareli': 'रायबरेली',
    'Rampur': 'रामपुर', 'Saharanpur': 'सहारनपुर', 'Sambhal': 'संभल',
    'Sant Kabir Nagar': 'संत कबीर नगर', 'Shahjahanpur': 'शाहजहांपुर', 'Shamli': 'शामली',
    'Shrawasti': 'श्रावस्ती', 'Siddharthnagar': 'सिद्धार्थनगर', 'Sitapur': 'सीतापुर',
    'Sonbhadra': 'सोनभद्र', 'Sultanpur': 'सुल्तानपुर', 'Unnao': 'उन्नाव',
    'Varanasi': 'वाराणसी',

    // Uttarakhand
    'Almora': 'अल्मोड़ा', 'Bageshwar': 'बागेश्वर', 'Chamoli': 'चमोली',
    'Champawat': 'चंपावत', 'Dehradun': 'देहरादून', 'Haridwar': 'हरिद्वार',
    'Nainital': 'नैनीताल', 'Pauri Garhwal': 'पौड़ी गढ़वाल', 'Pithoragarh': 'पिथौरागढ़',
    'Rudraprayag': 'रुद्रप्रयाग', 'Tehri Garhwal': 'टिहरी गढ़वाल',
    'Udham Singh Nagar': 'उधम सिंह नगर', 'Uttarkashi': 'उत्तरकाशी',

    // West Bengal
    'Alipurduar': 'अलीपुरद्वार', 'Bankura': 'बांकुड़ा', 'Birbhum': 'बीरभूम',
    'Cooch Behar': 'कूचबिहार', 'Dakshin Dinajpur': 'दक्षिण दिनाजपुर',
    'Darjeeling': 'दार्जिलिंग', 'Hooghly': 'हुगली', 'Howrah': 'हावड़ा',
    'Jalpaiguri': 'जलपाईगुड़ी', 'Jhargram': 'झारग्राम', 'Kalimpong': 'कालिम्पोंग',
    'Kolkata': 'कोलकाता', 'Malda': 'मालदा', 'Murshidabad': 'मुर्शिदाबाद', 'Nadia': 'नदिया',
    'North 24 Parganas': 'उत्तर 24 परगना', 'Paschim Bardhaman': 'पश्चिम बर्धमान',
    'Paschim Medinipur': 'पश्चिम मेदिनीपुर', 'Purba Bardhaman': 'पूर्व बर्धमान',
    'Purba Medinipur': 'पूर्व मेदिनीपुर', 'Purulia': 'पुरुलिया',
    'South 24 Parganas': 'दक्षिण 24 परगना', 'Uttar Dinajpur': 'उत्तर दिनाजपुर',
};

// ═══════════════════════════════════════════════════════════════════════
// TAMIL (ta-IN) — Tamil Nadu + Puducherry
// ═══════════════════════════════════════════════════════════════════════
DT['ta-IN'] = {
    'Ariyalur': 'அரியலூர்', 'Chengalpattu': 'செங்கல்பட்டு', 'Chennai': 'சென்னை',
    'Coimbatore': 'கோயம்புத்தூர்', 'Cuddalore': 'கடலூர்', 'Dharmapuri': 'தர்மபுரி',
    'Dindigul': 'திண்டுக்கல்', 'Erode': 'ஈரோடு', 'Kallakurichi': 'கள்ளக்குறிச்சி',
    'Kancheepuram': 'காஞ்சிபுரம்', 'Karur': 'கரூர்', 'Krishnagiri': 'கிருஷ்ணகிரி',
    'Madurai': 'மதுரை', 'Mayiladuthurai': 'மயிலாடுதுறை', 'Nagapattinam': 'நாகப்பட்டினம்',
    'Namakkal': 'நாமக்கல்', 'Nilgiris': 'நீலகிரி', 'Perambalur': 'பெரம்பலூர்',
    'Pudukkottai': 'புதுக்கோட்டை', 'Ramanathapuram': 'ராமநாதபுரம்', 'Ranipet': 'ராணிப்பேட்டை',
    'Salem': 'சேலம்', 'Sivaganga': 'சிவகங்கை', 'Tenkasi': 'தென்காசி',
    'Thanjavur': 'தஞ்சாவூர்', 'Theni': 'தேனி', 'Thoothukudi': 'தூத்துக்குடி',
    'Tiruchirappalli': 'திருச்சிராப்பள்ளி', 'Tirunelveli': 'திருநெல்வேலி',
    'Tirupathur': 'திருப்பத்தூர்', 'Tiruppur': 'திருப்பூர்', 'Tiruvallur': 'திருவள்ளூர்',
    'Tiruvannamalai': 'திருவண்ணாமலை', 'Tiruvarur': 'திருவாரூர்', 'Vellore': 'வேலூர்',
    'Viluppuram': 'விழுப்புரம்', 'Virudhunagar': 'விருதுநகர்',
    // Puducherry
    'Puducherry': 'புதுச்சேரி', 'Karaikal': 'காரைக்கால்', 'Mahe': 'மாஹே', 'Yanam': 'யானம்',
};

// ═══════════════════════════════════════════════════════════════════════
// TELUGU (te-IN) — Andhra Pradesh + Telangana
// ═══════════════════════════════════════════════════════════════════════
DT['te-IN'] = {
    // Andhra Pradesh
    'Anantapur': 'అనంతపురం', 'Chittoor': 'చిత్తూరు', 'East Godavari': 'తూర్పు గోదావరి',
    'Guntur': 'గుంటూరు', 'Krishna': 'కృష్ణా', 'Kurnool': 'కర్నూలు', 'Nellore': 'నెల్లూరు',
    'Prakasam': 'ప్రకాశం', 'Srikakulam': 'శ్రీకాకుళం', 'Visakhapatnam': 'విశాఖపట్నం',
    'Vizianagaram': 'విజయనగరం', 'West Godavari': 'పశ్చిమ గోదావరి', 'YSR Kadapa': 'వైఎస్ఆర్ కడప',
    'Alluri Sitharama Raju': 'అల్లూరి సీతారామరాజు', 'Anakapalli': 'అనకాపల్లి',
    'Bapatla': 'బాపట్ల', 'Eluru': 'ఏలూరు', 'Kakinada': 'కాకినాడ', 'Konaseema': 'కోనసీమ',
    'NTR': 'ఎన్టీఆర్', 'Palnadu': 'పల్నాడు', 'Parvathipuram Manyam': 'పార్వతీపురం మన్యం',
    'Sri Sathya Sai': 'శ్రీ సత్యసాయి', 'Tirupati': 'తిరుపతి',
    // Telangana
    'Adilabad': 'ఆదిలాబాద్', 'Bhadradri Kothagudem': 'భద్రాద్రి కొత్తగూడెం',
    'Hyderabad': 'హైదరాబాద్', 'Jagtial': 'జగిత్యాల', 'Jangaon': 'జనగాం',
    'Jayashankar Bhupalpally': 'జయశంకర్ భూపాలపల్లి', 'Jogulamba Gadwal': 'జోగులాంబ గద్వాల',
    'Kamareddy': 'కామారెడ్డి', 'Karimnagar': 'కరీంనగర్', 'Khammam': 'ఖమ్మం',
    'Komaram Bheem': 'కొమరం భీం', 'Mahabubabad': 'మహబూబాబాద్', 'Mahbubnagar': 'మహబూబ్‌నగర్',
    'Mancherial': 'మంచిర్యాల', 'Medak': 'మెదక్', 'Medchal-Malkajgiri': 'మేడ్చల్-మల్కాజ్‌గిరి',
    'Mulugu': 'ములుగు', 'Nagarkurnool': 'నాగర్‌కర్నూల్', 'Nalgonda': 'నల్గొండ',
    'Narayanpet': 'నారాయణపేట', 'Nirmal': 'నిర్మల్', 'Nizamabad': 'నిజామాబాద్',
    'Peddapalli': 'పెద్దపల్లి', 'Rajanna Sircilla': 'రాజన్న సిరిసిల్ల',
    'Rangareddy': 'రంగారెడ్డి', 'Sangareddy': 'సంగారెడ్డి', 'Siddipet': 'సిద్దిపేట',
    'Suryapet': 'సూర్యాపేట', 'Vikarabad': 'వికారాబాద్', 'Wanaparthy': 'వనపర్తి',
    'Warangal Rural': 'వరంగల్ గ్రామీణ', 'Warangal Urban': 'వరంగల్ నగరం',
    'Yadadri Bhuvanagiri': 'యాదాద్రి భువనగిరి',
};

// ═══════════════════════════════════════════════════════════════════════
// KANNADA (kn-IN) — Karnataka
// ═══════════════════════════════════════════════════════════════════════
DT['kn-IN'] = {
    'Bagalkot': 'ಬಾಗಲಕೋಟೆ', 'Bangalore Rural': 'ಬೆಂಗಳೂರು ಗ್ರಾಮೀಣ',
    'Bangalore Urban': 'ಬೆಂಗಳೂರು ನಗರ', 'Belgaum': 'ಬೆಳಗಾವಿ', 'Bellary': 'ಬಳ್ಳಾರಿ',
    'Bidar': 'ಬೀದರ್', 'Chamarajanagar': 'ಚಾಮರಾಜನಗರ', 'Chikkaballapur': 'ಚಿಕ್ಕಬಳ್ಳಾಪುರ',
    'Chikkamagaluru': 'ಚಿಕ್ಕಮಗಳೂರು', 'Chitradurga': 'ಚಿತ್ರದುರ್ಗ',
    'Dakshina Kannada': 'ದಕ್ಷಿಣ ಕನ್ನಡ', 'Davanagere': 'ದಾವಣಗೆರೆ', 'Dharwad': 'ಧಾರವಾಡ',
    'Gadag': 'ಗದಗ', 'Hassan': 'ಹಾಸನ', 'Haveri': 'ಹಾವೇರಿ', 'Kalaburagi': 'ಕಲಬುರಗಿ',
    'Kodagu': 'ಕೊಡಗು', 'Kolar': 'ಕೋಲಾರ', 'Koppal': 'ಕೊಪ್ಪಳ', 'Mandya': 'ಮಂಡ್ಯ',
    'Mysore': 'ಮೈಸೂರು', 'Raichur': 'ರಾಯಚೂರು', 'Ramanagara': 'ರಾಮನಗರ',
    'Shimoga': 'ಶಿವಮೊಗ್ಗ', 'Tumkur': 'ತುಮಕೂರು', 'Udupi': 'ಉಡುಪಿ',
    'Uttara Kannada': 'ಉತ್ತರ ಕನ್ನಡ', 'Vijayapura': 'ವಿಜಯಪುರ', 'Yadgir': 'ಯಾದಗಿರಿ',
};

// ═══════════════════════════════════════════════════════════════════════
// MALAYALAM (ml-IN) — Kerala
// ═══════════════════════════════════════════════════════════════════════
DT['ml-IN'] = {
    'Alappuzha': 'ആലപ്പുഴ', 'Ernakulam': 'എറണാകുളം', 'Idukki': 'ഇടുക്കി',
    'Kannur': 'കണ്ണൂർ', 'Kasaragod': 'കാസർഗോഡ്', 'Kollam': 'കൊല്ലം',
    'Kottayam': 'കോട്ടയം', 'Kozhikode': 'കോഴിക്കോട്', 'Malappuram': 'മലപ്പുറം',
    'Palakkad': 'പാലക്കാട്', 'Pathanamthitta': 'പത്തനംതിട്ട',
    'Thiruvananthapuram': 'തിരുവനന്തപുരം', 'Thrissur': 'തൃശ്ശൂർ', 'Wayanad': 'വയനാട്',
};

// ═══════════════════════════════════════════════════════════════════════
// BENGALI (bn-IN) — West Bengal + Tripura
// ═══════════════════════════════════════════════════════════════════════
DT['bn-IN'] = {
    // West Bengal
    'Alipurduar': 'আলিপুরদুয়ার', 'Bankura': 'বাঁকুড়া', 'Birbhum': 'বীরভূম',
    'Cooch Behar': 'কোচবিহার', 'Dakshin Dinajpur': 'দক্ষিণ দিনাজপুর',
    'Darjeeling': 'দার্জিলিং', 'Hooghly': 'হুগলি', 'Howrah': 'হাওড়া',
    'Jalpaiguri': 'জলপাইগুড়ি', 'Jhargram': 'ঝাড়গ্রাম', 'Kalimpong': 'কালিম্পং',
    'Kolkata': 'কলকাতা', 'Malda': 'মালদা', 'Murshidabad': 'মুর্শিদাবাদ', 'Nadia': 'নদিয়া',
    'North 24 Parganas': 'উত্তর ২৪ পরগনা', 'Paschim Bardhaman': 'পশ্চিম বর্ধমান',
    'Paschim Medinipur': 'পশ্চিম মেদিনীপুর', 'Purba Bardhaman': 'পূর্ব বর্ধমান',
    'Purba Medinipur': 'পূর্ব মেদিনীপুর', 'Purulia': 'পুরুলিয়া',
    'South 24 Parganas': 'দক্ষিণ ২৪ পরগনা', 'Uttar Dinajpur': 'উত্তর দিনাজপুর',
    // Tripura
    'Dhalai': 'ধলাই', 'Gomati': 'গোমতী', 'Khowai': 'খোয়াই',
    'North Tripura': 'উত্তর ত্রিপুরা', 'Sepahijala': 'সিপাহীজলা',
    'South Tripura': 'দক্ষিণ ত্রিপুরা', 'Unakoti': 'উনকোটি', 'West Tripura': 'পশ্চিম ত্রিপুরা',
};

// ═══════════════════════════════════════════════════════════════════════
// MARATHI (mr-IN) — Maharashtra
// ═══════════════════════════════════════════════════════════════════════
DT['mr-IN'] = {
    'Ahmednagar': 'अहमदनगर', 'Akola': 'अकोला', 'Amravati': 'अमरावती',
    'Aurangabad': 'औरंगाबाद', 'Beed': 'बीड', 'Bhandara': 'भंडारा', 'Buldhana': 'बुलढाणा',
    'Chandrapur': 'चंद्रपूर', 'Dhule': 'धुळे', 'Gadchiroli': 'गडचिरोली', 'Gondia': 'गोंदिया',
    'Hingoli': 'हिंगोली', 'Jalgaon': 'जळगाव', 'Jalna': 'जालना', 'Kolhapur': 'कोल्हापूर',
    'Latur': 'लातूर', 'Mumbai City': 'मुंबई शहर', 'Mumbai Suburban': 'मुंबई उपनगर',
    'Nagpur': 'नागपूर', 'Nanded': 'नांदेड', 'Nandurbar': 'नंदुरबार', 'Nashik': 'नाशिक',
    'Osmanabad': 'उस्मानाबाद', 'Palghar': 'पालघर', 'Parbhani': 'परभणी', 'Pune': 'पुणे',
    'Raigad': 'रायगड', 'Ratnagiri': 'रत्नागिरी', 'Sangli': 'सांगली', 'Satara': 'सातारा',
    'Sindhudurg': 'सिंधुदुर्ग', 'Solapur': 'सोलापूर', 'Thane': 'ठाणे', 'Wardha': 'वर्धा',
    'Washim': 'वाशिम', 'Yavatmal': 'यवतमाळ',
};

// ═══════════════════════════════════════════════════════════════════════
// GUJARATI (gu-IN) — Gujarat
// ═══════════════════════════════════════════════════════════════════════
DT['gu-IN'] = {
    'Ahmedabad': 'અમદાવાદ', 'Amreli': 'અમરેલી', 'Anand': 'આણંદ', 'Aravalli': 'અરવલ્લી',
    'Banaskantha': 'બનાસકાંઠા', 'Bharuch': 'ભરૂચ', 'Bhavnagar': 'ભાવનગર', 'Botad': 'બોટાદ',
    'Chhota Udaipur': 'છોટા ઉદેપુર', 'Dahod': 'દાહોદ', 'Dang': 'ડાંગ',
    'Devbhumi Dwarka': 'દેવભૂમિ દ્વારકા', 'Gandhinagar': 'ગાંધીનગર',
    'Gir Somnath': 'ગીર સોમનાથ', 'Jamnagar': 'જામનગર', 'Junagadh': 'જૂનાગઢ',
    'Kutch': 'કચ્છ', 'Kheda': 'ખેડા', 'Mahisagar': 'મહીસાગર', 'Mehsana': 'મહેસાણા',
    'Morbi': 'મોરબી', 'Narmada': 'નર્મદા', 'Navsari': 'નવસારી', 'Panchmahal': 'પંચમહાલ',
    'Patan': 'પાટણ', 'Porbandar': 'પોરબંદર', 'Rajkot': 'રાજકોટ',
    'Sabarkantha': 'સાબરકાંઠા', 'Surat': 'સુરત', 'Surendranagar': 'સુરેન્દ્રનગર',
    'Tapi': 'તાપી', 'Vadodara': 'વડોદરા', 'Valsad': 'વલસાડ',
};

// ═══════════════════════════════════════════════════════════════════════
// PUNJABI (pa-IN) — Punjab
// ═══════════════════════════════════════════════════════════════════════
DT['pa-IN'] = {
    'Amritsar': 'ਅੰਮ੍ਰਿਤਸਰ', 'Barnala': 'ਬਰਨਾਲਾ', 'Bathinda': 'ਬਠਿੰਡਾ',
    'Faridkot': 'ਫਰੀਦਕੋਟ', 'Fatehgarh Sahib': 'ਫਤਹਿਗੜ੍ਹ ਸਾਹਿਬ', 'Fazilka': 'ਫ਼ਾਜ਼ਿਲਕਾ',
    'Ferozepur': 'ਫਿਰੋਜ਼ਪੁਰ', 'Gurdaspur': 'ਗੁਰਦਾਸਪੁਰ', 'Hoshiarpur': 'ਹੁਸ਼ਿਆਰਪੁਰ',
    'Jalandhar': 'ਜਲੰਧਰ', 'Kapurthala': 'ਕਪੂਰਥਲਾ', 'Ludhiana': 'ਲੁਧਿਆਣਾ',
    'Malerkotla': 'ਮਲੇਰਕੋਟਲਾ', 'Mansa': 'ਮਾਨਸਾ', 'Moga': 'ਮੋਗਾ', 'Mohali': 'ਮੋਹਾਲੀ',
    'Muktsar': 'ਮੁਕਤਸਰ', 'Pathankot': 'ਪਠਾਨਕੋਟ', 'Patiala': 'ਪਟਿਆਲਾ',
    'Rupnagar': 'ਰੂਪਨਗਰ', 'Sangrur': 'ਸੰਗਰੂਰ',
    'Shaheed Bhagat Singh Nagar': 'ਸ਼ਹੀਦ ਭਗਤ ਸਿੰਘ ਨਗਰ', 'Tarn Taran': 'ਤਰਨ ਤਾਰਨ',
};

// ═══════════════════════════════════════════════════════════════════════
// ODIA (or-IN) — Odisha
// ═══════════════════════════════════════════════════════════════════════
DT['or-IN'] = {
    'Angul': 'ଅନୁଗୁଳ', 'Balangir': 'ବଲାଙ୍ଗୀର', 'Balasore': 'ବାଲେଶ୍ୱର',
    'Bargarh': 'ବରଗଡ଼', 'Bhadrak': 'ଭଦ୍ରକ', 'Boudh': 'ବୌଦ୍ଧ', 'Cuttack': 'କଟକ',
    'Deogarh': 'ଦେଓଗଡ଼', 'Dhenkanal': 'ଢେଙ୍କାନାଳ', 'Gajapati': 'ଗଜପତି',
    'Ganjam': 'ଗଞ୍ଜାମ', 'Jagatsinghpur': 'ଜଗତସିଂହପୁର', 'Jajpur': 'ଯାଜପୁର',
    'Jharsuguda': 'ଝାରସୁଗୁଡ଼ା', 'Kalahandi': 'କଳାହାଣ୍ଡି', 'Kandhamal': 'କନ୍ଧମାଳ',
    'Kendrapara': 'କେନ୍ଦ୍ରାପଡ଼ା', 'Kendujhar': 'କେନ୍ଦୁଝର', 'Khordha': 'ଖୋର୍ଦ୍ଧା',
    'Koraput': 'କୋରାପୁଟ', 'Malkangiri': 'ମାଲକାନଗିରି', 'Mayurbhanj': 'ମୟୂରଭଞ୍ଜ',
    'Nabarangpur': 'ନବରଙ୍ଗପୁର', 'Nayagarh': 'ନୟାଗଡ଼', 'Nuapada': 'ନୂଆପଡ଼ା',
    'Puri': 'ପୁରୀ', 'Rayagada': 'ରାୟଗଡ଼ା', 'Sambalpur': 'ସମ୍ବଲପୁର',
    'Subarnapur': 'ସୁବର୍ଣ୍ଣପୁର', 'Sundargarh': 'ସୁନ୍ଦରଗଡ଼',
};

// ═══════════════════════════════════════════════════════════════════════
// ASSAMESE (as-IN) — Assam
// ═══════════════════════════════════════════════════════════════════════
DT['as-IN'] = {
    'Baksa': 'বাক্সা', 'Barpeta': 'বৰপেটা', 'Bongaigaon': 'বঙাইগাঁও', 'Cachar': 'কাছাৰ',
    'Chirang': 'চিৰাং', 'Darrang': 'দৰং', 'Dhemaji': 'ধেমাজি', 'Dhubri': 'ধুবুৰী',
    'Dibrugarh': 'ডিব্ৰুগড়', 'Dima Hasao': 'ডিমা হাছাও', 'Goalpara': 'গোৱালপাৰা',
    'Golaghat': 'গোলাঘাট', 'Hailakandi': 'হাইলাকান্দি', 'Jorhat': 'যোৰহাট',
    'Kamrup': 'কামৰূপ', 'Kamrup Metropolitan': 'কামৰূপ মহানগৰ',
    'Karbi Anglong': 'কাৰ্বি আংলং', 'Karimganj': 'করিমগঞ্জ', 'Kokrajhar': 'কোকৰাঝাৰ',
    'Lakhimpur': 'লখিমপুৰ', 'Morigaon': 'মৰিগাঁও', 'Nagaon': 'নগাঁও',
    'Nalbari': 'নলবাৰী', 'Sivasagar': 'শিৱসাগৰ', 'Sonitpur': 'শোণিতপুৰ',
    'Tinsukia': 'তিনিচুকীয়া', 'Udalguri': 'উদালগুৰি',
};

/**
 * Get the translated district name for the given language.
 * Falls back: language → Hindi → English (original).
 */
export function getDistrictName(district, language) {
    if (!district) return '';
    if (language === 'en-IN') return district;
    return DT[language]?.[district] || DT['hi-IN']?.[district] || district;
}

// ═══════════════════════════════════════════════════════════════════════
// Common city name aliases (alternate spellings used in weather/maps)
// Added to Hindi + relevant regional languages
// ═══════════════════════════════════════════════════════════════════════
const CITY_ALIASES_HI = {
    'Delhi': 'दिल्ली', 'New Delhi': 'नई दिल्ली', 'Mumbai': 'मुंबई',
    'Bangalore': 'बेंगलूरु', 'Bengaluru': 'बेंगलूरु',
    'Chandigarh': 'चंडीगढ़', 'Guwahati': 'गुवाहाटी',
    'Bhubaneswar': 'भुवनेश्वर', 'Trichy': 'तिरुचिरापल्ली',
    'Thiruvananthapuram': 'तिरुवनंतपुरम',
};
Object.assign(DT['hi-IN'], CITY_ALIASES_HI);

// Tamil aliases
Object.assign(DT['ta-IN'], {
    'Delhi': 'டெல்லி', 'New Delhi': 'புது டெல்லி', 'Mumbai': 'மும்பை',
    'Bangalore': 'பெங்களூரு', 'Bengaluru': 'பெங்களூரு',
    'Kolkata': 'கொல்கத்தா', 'Hyderabad': 'ஹைதராபாத்',
    'Chandigarh': 'சண்டிகர்', 'Guwahati': 'குவாஹாட்டி',
    'Bhubaneswar': 'புவனேஸ்வர்', 'Trichy': 'திருச்சி',
    'Thiruvananthapuram': 'திருவனந்தபுரம்',
    'Ahmedabad': 'அகமதாபாத்', 'Pune': 'புனே', 'Jaipur': 'ஜெய்ப்பூர்',
    'Lucknow': 'லக்னோ', 'Bhopal': 'போபால்', 'Patna': 'பட்னா',
    'Raipur': 'ராய்ப்பூர்', 'Ranchi': 'ராஞ்சி',
});

// Telugu aliases
Object.assign(DT['te-IN'], {
    'Delhi': 'ఢిల్లీ', 'New Delhi': 'న్యూ ఢిల్లీ', 'Mumbai': 'ముంబై',
    'Bangalore': 'బెంగళూరు', 'Bengaluru': 'బెంగళూరు',
    'Kolkata': 'కోల్‌కతా', 'Chennai': 'చెన్నై',
    'Chandigarh': 'చండీగఢ్', 'Guwahati': 'గువాహాటి',
    'Bhubaneswar': 'భువనేశ్వర్', 'Trichy': 'తిరుచ్చి',
    'Thiruvananthapuram': 'తిరువనంతపురం',
    'Ahmedabad': 'అహ్మదాబాద్', 'Pune': 'పుణె', 'Jaipur': 'జైపూర్',
    'Lucknow': 'లక్నో', 'Bhopal': 'భోపాల్', 'Patna': 'పాట్నా',
    'Raipur': 'రాయ్‌పూర్', 'Ranchi': 'రాంచీ',
    'Coimbatore': 'కోయంబత్తూరు', 'Salem': 'సేలం', 'Madurai': 'మదురై',
});

// Kannada aliases
Object.assign(DT['kn-IN'], {
    'Delhi': 'ದೆಹಲಿ', 'New Delhi': 'ನವ ದೆಹಲಿ', 'Mumbai': 'ಮುಂಬೈ',
    'Bangalore': 'ಬೆಂಗಳೂರು', 'Bengaluru': 'ಬೆಂಗಳೂರು',
    'Kolkata': 'ಕೊಲ್ಕತ್ತಾ', 'Chennai': 'ಚೆನ್ನೈ', 'Hyderabad': 'ಹೈದರಾಬಾದ್',
    'Chandigarh': 'ಚಂಡೀಗಡ', 'Guwahati': 'ಗುವಾಹಟಿ',
    'Bhubaneswar': 'ಭುವನೇಶ್ವರ', 'Trichy': 'ತಿರುಚ್ಚಿ',
    'Thiruvananthapuram': 'ತಿರುವನಂತಪುರಂ',
    'Ahmedabad': 'ಅಹಮದಾಬಾದ್', 'Pune': 'ಪುಣೆ', 'Jaipur': 'ಜೈಪುರ',
    'Lucknow': 'ಲಕ್ನೋ', 'Bhopal': 'ಭೋಪಾಲ್', 'Patna': 'ಪಾಟ್ನಾ',
    'Raipur': 'ರಾಯ್‌ಪುರ', 'Ranchi': 'ರಾಂಚಿ',
    'Coimbatore': 'ಕೋಯಂಬತ್ತೂರು', 'Salem': 'ಸೇಲಂ', 'Madurai': 'ಮದುರೈ',
    'Visakhapatnam': 'ವಿಶಾಖಪಟ್ಟಣಂ',
});

// Malayalam aliases
Object.assign(DT['ml-IN'], {
    'Delhi': 'ഡൽഹി', 'New Delhi': 'ന്യൂ ഡൽഹി', 'Mumbai': 'മുംബൈ',
    'Bangalore': 'ബെംഗളൂരു', 'Bengaluru': 'ബെംഗളൂരു',
    'Kolkata': 'കൊൽക്കത്ത', 'Chennai': 'ചെന്നൈ', 'Hyderabad': 'ഹൈദരാബാദ്',
    'Chandigarh': 'ചണ്ഡീഗഡ്', 'Guwahati': 'ഗുവാഹാത്തി',
    'Bhubaneswar': 'ഭുവനേശ്വർ', 'Trichy': 'തിരുച്ചി',
    'Ahmedabad': 'അഹമ്മദാബാദ്', 'Pune': 'പൂനെ', 'Jaipur': 'ജയ്‌പുർ',
    'Lucknow': 'ലഖ്‌നൗ', 'Bhopal': 'ഭോപ്പാൽ', 'Patna': 'പട്‌ന',
    'Raipur': 'റായ്‌പൂർ', 'Ranchi': 'റാഞ്ചി',
    'Coimbatore': 'കോയമ്പത്തൂർ', 'Salem': 'സേലം', 'Madurai': 'മധുരൈ',
    'Visakhapatnam': 'വിശാഖപട്ടണം',
});

// Bengali aliases
Object.assign(DT['bn-IN'], {
    'Delhi': 'দিল্লি', 'New Delhi': 'নতুন দিল্লি', 'Mumbai': 'মুম্বাই',
    'Bangalore': 'ব্যাঙ্গালোর', 'Bengaluru': 'বেঙ্গালুরু',
    'Chennai': 'চেন্নাই', 'Hyderabad': 'হায়দরাবাদ',
    'Chandigarh': 'চণ্ডীগড়', 'Guwahati': 'গুয়াহাটি',
    'Bhubaneswar': 'ভুবনেশ্বর', 'Trichy': 'তিরুচিরাপল্লি',
    'Thiruvananthapuram': 'তিরুবনন্তপুরম',
    'Ahmedabad': 'আহমেদাবাদ', 'Pune': 'পুনে', 'Jaipur': 'জয়পুর',
    'Lucknow': 'লখনৌ', 'Bhopal': 'ভোপাল', 'Patna': 'পাটনা',
    'Raipur': 'রায়পুর', 'Ranchi': 'রাঁচি',
    'Coimbatore': 'কোয়েম্বাটুর', 'Salem': 'সেলেম', 'Madurai': 'মাদুরাই',
    'Visakhapatnam': 'বিশাখাপত্তনম',
});

// Marathi aliases
Object.assign(DT['mr-IN'], {
    'Delhi': 'दिल्ली', 'New Delhi': 'नवी दिल्ली', 'Mumbai': 'मुंबई',
    'Bangalore': 'बेंगळूरू', 'Bengaluru': 'बेंगळूरू',
    'Kolkata': 'कोलकाता', 'Chennai': 'चेन्नई', 'Hyderabad': 'हैदराबाद',
    'Chandigarh': 'चंदीगड', 'Guwahati': 'गुवाहाटी',
    'Bhubaneswar': 'भुवनेश्वर', 'Trichy': 'तिरुचिरापल्ली',
    'Thiruvananthapuram': 'तिरुवनंतपुरम',
    'Ahmedabad': 'अहमदाबाद', 'Jaipur': 'जयपूर',
    'Lucknow': 'लखनौ', 'Bhopal': 'भोपाळ', 'Patna': 'पाटणा',
    'Raipur': 'रायपूर', 'Ranchi': 'रांची',
    'Coimbatore': 'कोइम्बतूर', 'Salem': 'सेलम', 'Madurai': 'मदुराई',
    'Visakhapatnam': 'विशाखापट्टणम',
});

// Gujarati aliases
Object.assign(DT['gu-IN'], {
    'Delhi': 'દિલ્હી', 'New Delhi': 'નવી દિલ્હી', 'Mumbai': 'મુંબઈ',
    'Bangalore': 'બેંગલુરુ', 'Bengaluru': 'બેંગલુરુ',
    'Kolkata': 'કોલકાતા', 'Chennai': 'ચેન્નાઈ', 'Hyderabad': 'હૈદરાબાદ',
    'Chandigarh': 'ચંદીગઢ', 'Guwahati': 'ગુવાહાટી',
    'Bhubaneswar': 'ભુવનેશ્વર', 'Trichy': 'તિરુચ્ચિ',
    'Thiruvananthapuram': 'તિરુવનંતપુરમ',
    'Pune': 'પૂણે', 'Jaipur': 'જયપુર',
    'Lucknow': 'લખનઉ', 'Bhopal': 'ભોપાલ', 'Patna': 'પટના',
    'Raipur': 'રાયપુર', 'Ranchi': 'રાંચી',
    'Coimbatore': 'કોઈમ્બતૂર', 'Salem': 'સેલમ', 'Madurai': 'મદુરાઈ',
    'Visakhapatnam': 'વિશાખાપટ્ટણમ',
});

// Punjabi aliases
Object.assign(DT['pa-IN'], {
    'Delhi': 'ਦਿੱਲੀ', 'New Delhi': 'ਨਵੀਂ ਦਿੱਲੀ', 'Mumbai': 'ਮੁੰਬਈ',
    'Bangalore': 'ਬੈਂਗਲੁਰੂ', 'Bengaluru': 'ਬੈਂਗਲੁਰੂ',
    'Kolkata': 'ਕੋਲਕਾਤਾ', 'Chennai': 'ਚੇਨਈ', 'Hyderabad': 'ਹੈਦਰਾਬਾਦ',
    'Chandigarh': 'ਚੰਡੀਗੜ੍ਹ', 'Guwahati': 'ਗੁਵਾਹਾਟੀ',
    'Bhubaneswar': 'ਭੁਵਨੇਸ਼ਵਰ', 'Trichy': 'ਤਿਰੁਚਿ',
    'Thiruvananthapuram': 'ਤਿਰੁਵਨੰਤਪੁਰਮ',
    'Ahmedabad': 'ਅਹਿਮਦਾਬਾਦ', 'Pune': 'ਪੁਣੇ', 'Jaipur': 'ਜੈਪੁਰ',
    'Lucknow': 'ਲਖਨਊ', 'Bhopal': 'ਭੋਪਾਲ', 'Patna': 'ਪਟਨਾ',
    'Raipur': 'ਰਾਏਪੁਰ', 'Ranchi': 'ਰਾਂਚੀ',
    'Coimbatore': 'ਕੋਇੰਬਟੂਰ', 'Salem': 'ਸੇਲਮ', 'Madurai': 'ਮਦੁਰੈ',
    'Visakhapatnam': 'ਵਿਸ਼ਾਖਾਪਟਨਮ',
});

// Odia aliases
Object.assign(DT['or-IN'], {
    'Delhi': 'ଦିଲ୍ଲୀ', 'New Delhi': 'ନୂଆ ଦିଲ୍ଲୀ', 'Mumbai': 'ମୁମ୍ବାଇ',
    'Bangalore': 'ବେଙ୍ଗାଲୁରୁ', 'Bengaluru': 'ବେଙ୍ଗାଲୁରୁ',
    'Kolkata': 'କୋଲକାତା', 'Chennai': 'ଚେନ୍ନାଇ', 'Hyderabad': 'ହୈଦ୍ରାବାଦ',
    'Chandigarh': 'ଚଣ୍ଡୀଗଡ଼', 'Guwahati': 'ଗୁଆହାଟୀ',
    'Bhubaneswar': 'ଭୁବନେଶ୍ୱର', 'Trichy': 'ତିରୁଚ୍ଚି',
    'Thiruvananthapuram': 'ତିରୁବନନ୍ତପୁରମ',
    'Ahmedabad': 'ଅହମଦାବାଦ', 'Pune': 'ପୁଣେ', 'Jaipur': 'ଜୟପୁର',
    'Lucknow': 'ଲଖନଊ', 'Bhopal': 'ଭୋପାଳ', 'Patna': 'ପାଟନା',
    'Raipur': 'ରାଇପୁର', 'Ranchi': 'ରାଞ୍ଚି',
    'Coimbatore': 'କୋଇମ୍ବାଟୁର', 'Salem': 'ସେଲମ', 'Madurai': 'ମାଦୁରାଇ',
    'Visakhapatnam': 'ବିଶାଖାପଟ୍ଟନମ',
});

// Assamese aliases
Object.assign(DT['as-IN'], {
    'Delhi': 'দিল্লী', 'New Delhi': 'নতুন দিল্লী', 'Mumbai': 'মুম্বাই',
    'Bangalore': 'বাংগালোৰ', 'Bengaluru': 'বেঙ্গালুৰু',
    'Kolkata': 'কলকাতা', 'Chennai': 'চেন্নাই', 'Hyderabad': 'হায়দৰাবাদ',
    'Chandigarh': 'চণ্ডীগড়', 'Bhubaneswar': 'ভুবনেশ্বৰ',
    'Trichy': 'তিৰুচিৰাপল্লী', 'Thiruvananthapuram': 'তিৰুবনন্তপুৰম',
    'Ahmedabad': 'আহমেদাবাদ', 'Pune': 'পুণে', 'Jaipur': 'জয়পুৰ',
    'Lucknow': 'লক্ষ্ণৌ', 'Bhopal': 'ভোপাল', 'Patna': 'পাটনা',
    'Raipur': 'ৰায়পুৰ', 'Ranchi': 'ৰাঁচী',
    'Coimbatore': 'কোয়েম্বাটুৰ', 'Salem': 'চেলম', 'Madurai': 'মাদুৰাই',
    'Visakhapatnam': 'বিশাখাপট্টনম',
});

// Urdu aliases
DT['ur-IN'] = {
    'Delhi': 'دہلی', 'New Delhi': 'نئی دہلی', 'Mumbai': 'ممبئی',
    'Bangalore': 'بنگلور', 'Bengaluru': 'بنگلور',
    'Kolkata': 'کولکاتا', 'Chennai': 'چنائی', 'Hyderabad': 'حیدرآباد',
    'Ahmedabad': 'احمد آباد', 'Pune': 'پونے', 'Jaipur': 'جے پور',
    'Lucknow': 'لکھنؤ', 'Chandigarh': 'چنڈی گڑھ', 'Bhopal': 'بھوپال',
    'Patna': 'پٹنا', 'Guwahati': 'گوہاٹی', 'Bhubaneswar': 'بھونیشور',
    'Raipur': 'رائے پور', 'Ranchi': 'رانچی', 'Trichy': 'تروچی',
    'Thiruvananthapuram': 'تروونانتپورم',
    'Coimbatore': 'کوئمبٹور', 'Salem': 'سیلم', 'Madurai': 'مدورائی',
    'Visakhapatnam': 'وشاکھاپٹنم',
};
