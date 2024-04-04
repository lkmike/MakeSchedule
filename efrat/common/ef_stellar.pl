#! /usr/bin/perl
use Time::Local;
use Switch;

my $num_azimuths = $ARGV[0] || 61; # vvedite zdes kol-vo azimutov dlja vybora faila scenariya i t.p.
my $beg_antenna = 30; # nachalo set antenna  v minutah
my $inputfile = $ARGV[1]злой шкаф || "efrat_sun.dat"; # vhodnoj fail s efemeridami
my $mainobsfile = $ARGV[2] || "mainobs_sun.txt"; # vyhodnoj fail s zadaniem dlja registracii
my $roundfile = $ARGV[3];# esli ne zadano, imya faila s zadaniem dlja krugovogo otrazhatelya formiruetsja avtomaticheski
my $flatfile = $ARGV[4];#esli ne zadano, imya faila s zadaniem dlja ploskogo otrazhatelya formiruetsja avtomaticheski
my $vynosfile = $ARGV[5] || "0"; # fail s velichinami vynosov v azimutah, format 30: -16
my $debug = 1;
my $perevod = 0; #prevod chasov na letnne-zimnee vremya

my $beg_mainobs1 = 1; #min nachalo vypolnenija zadanja ot nachala zapisi
my $beg_mainobs_roof = 10; #min
my $end_mainobs_roof = 7; #min
my $beg_mainobs_gsh = 2; #min
my $firstchar = 0;
if (index($inputfile,'a') eq 0) {
    $firstchar++;
}
my $object = substr($inputfile, $firstchar, index($inputfile, '_') - $firstchar) || "Sun";
print "object:'$object'\n";
#my $object="Sun";
#my $object_lower="sun";
my $object_lower = lc($object);
if (($object_lower ne 'sun') and ($object_lower ne 'moon')) {
    $num_azimuths=-1;
}

my $scenfile = "is not set!!!";

switch($num_azimuths){
    case -1 { #sidereal sources
        $beg_mainobs_roof=35;#min
        $end_mainobs_roof=5; #min
        $duration="-1.5/1.5"; #min dlja mnozoazimutalnyh nabljudenij (31-61 azimut v den)
        $beg_mainobs2=1;#min  dlja 61 azimutov #nachalo nabljudenij ( minuty) do kulminacii
        $beg_mainobs2_sec=30;#sec  dlja 61 azimutov #nachalo nabljudenij (sekundy) do kulminacii
        $scenfile="z_krab_180"; #dlja 61 azimutov
        $csmode="STD+Prep"; #dlja 31-61 azimutov
        $parabola="P"; #dlja 31-61 azimutov
        print "Number of azimuths: $num_azimuths \n";
    }
    case 61 {
        $beg_mainobs_roof=35;#min
        $end_mainobs_roof=5; #min
        $duration="-1.5/1.5"; #min dlja mnozoazimutalnyh nabljudenij (31-61 azimut v den)
        # $duration="-1.5/2"; #min dlja bolee dlinnyh zapisej
        $beg_mainobs2=1;#min  dlja 61 azimutov #nachalo nabljudenij ( minuty) do kulminacii
        $beg_mainobs2_sec=30;#sec  dlja 61 azimutov #nachalo nabljudenij (sekundy) do kulminacii
        $scenfile="z_sun_180"; #dlja 61 azimutov
        $csmode="STD+Prep"; #dlja 31-61 azimutov
        $parabola="Q"; #dlja 31-61 azimutov
        print "Number of azimuths: $num_azimuths \n";
    }
    case 31 {
        $duration="-1.5/1.5"; #min
        $duration="-1/1.4"; #min
        $beg_mainobs2=2;#min  dlja 31 azimutov
        $beg_mainobs2_sec=0;#  dlja azimutov < 61
        $scenfile="z_sun_240"; #dlja 31 azimutov
        $csmode="STD+Prep"; #dlja 31-61 azimutov
        $parabola="P"; #dlja 31-61 azimutov
        print "Number of azimuths: $num_azimuths\n";
    }
    case [1..5] {
        $duration="-5/5"; #min
        $beg_mainobs2=5;#min  dlja 1-5 azimutov
        $beg_mainobs2_sec=0;#  dlja azimutov < 61
        $scenfile="z_sun_600"; #dlja 31 azimutov
        $csmode="STD"; #dlja < 31 azimutov
        $parabola="P"; #dlja < 31 azimutov
        print "Number of azimuths: $num_azimuths\n";
    }
    case [6..15] {
        $duration="-4/4"; #min
        $beg_mainobs2=4;#min  dlja 1-5 azimutov
        $beg_mainobs2_sec=0;#  dlja azimutov < 61
        $scenfile="z_sun_480"; #dlja 31 azimutov
        $csmode="STD+Prep"; #dlja < 31 azimutov
        $parabola="P"; #dlja < 31 azimutov
        print "Number of azimuths: $num_azimuths\n";
    }
    else {
        print "Number of azimuths is not set!!";
    }
}

%M = qw(Jan 0 Feb 1 Mar 2 Apr 3 May 4 Jun 5 Jul 6 Aug 7 Sep 8 Oct 9 Nov 10 Dec 11);
%W = qw(Sun ����������� Mon ����������� Tue ������� Wed ����� Thu ������� Fri ������� Sat �������);

open(FILE, $inputfile) || die "������� ���� $inputfile �� ������!";;
my @file = <FILE>;
close(FILE);
$col = @file;
$s1 = @file[0];
$s2 = @file[$col - 1];
#print $s1;
#print $s2;
($begin, $year, $month, $day, $hour, $min, $sec, @sh) = split(/\s+/, $s1);
($begin, $year2, $month2, $day2, $hour2, $min2, $sec2, @sh) = split(/\s+/, $s2);
$hour = $hour + $perevod;
$hour2 = $hour2 + $perevod;
                 
#if ($sec-60 ge 0 ) {$sec=$sec-60.0; $min++;}
#if ($sec2-60 ge 0 ) {$sec2=$sec2-60.0; $min++;}
#if ($sec2-60 ge 0 ) {$sec=$sec2-60.0; $min++;}
if ($sec - 59.5 ge 0 ) {
    $sec = $sec - 59.5; 
    $min++;
}
if ($sec2 - 59.5 ge 0 ) {
    $sec2 = $sec2 - 59.5; 
    $min2++;
}
if ($hour lt 0 ) {
    $hour = $hour + 24;
}
if ($hour2 lt 0 ) {
    $hour2 = $hour2 + 24;
}


my $time1 = timelocal($sec, $min, $hour, $day, $month - 1, $year);
## Patch to fix Efrat 1-hour issue
$time1 -= 3600;

my $time2 = timelocal($sec2, $min2, $hour2, $day2, $month2 - 1, $year2);
## Patch to fix Efrat 1-hour issue
$time2 -= 3600;

$time1 = $time1 - $beg_antenna * 60;
$time2 = $time2 + $beg_antenna * 60;
@timestamp1 = split(/\s+/, localtime($time1));
@timestamp2 = split(/\s+/, localtime($time2));
#YMDDc.csi
$targetfil = sprintf("%s%x%02ds.csi", substr($year, 3, 1), $month, $day);
$targetflatfil = sprintf("%s%x%02df.csi", substr($year, 3, 1), $month, $day);
my $roundfile = $ARGV[3] || $targetfil;
my $flatfile = $ARGV[4] || $targetflatfil;
print "��: $inputfile \t ���: 1) $mainobsfile \t 2) $roundfile\t 3) $flatfile\n";
open (ROUNDFILE, ">$roundfile");
open (MAINOBSFILE, ">$mainobsfile");
open (FLATFILE, ">$flatfile");
print ROUNDFILE "Problem  = SunObs\n";
print ROUNDFILE "----------------------------------------------\n";
print ROUNDFILE "Term\tBegDate\tBegTime\tEndDate\tEndTime\n";
print ROUNDFILE "----------------------------------------------\n";
printf ROUNDFILE "set\t%0d.%02d.%02d %s %0d.%02d.%02d %s\n\n", $timestamp1[4], $M{$timestamp1[1]} + 1, 
    $timestamp1[2],  $timestamp1[3], $timestamp2[4], $M{$timestamp2[1]} + 1,  $timestamp2[2],  
    $timestamp2[3];
print ROUNFILE "----------------------------------------------\n";
print ROUNDFILE "Nmin     = 100\n";
print ROUNDFILE "Include  = JoinPAR.csi\n\n";
print ROUNDFILE "Feed     = 3\n";
print ROUNDFILE "AzF      = S+P\n";
print ROUNDFILE "Class    = Setting\n";
printf ROUNDFILE "CSmode   = %s\n", $csmode;
print ROUNDFILE "Altitude =   0:00:00\n";
print ROUNDFILE "Azimuth  = 180:00:00\n";
print ROUNDFILE "Focus    = 0\n";
print ROUNDFILE "Duration = $duration\n\n";
print ROUNDFILE "--------------------------------------------------------------------\n";
print ROUNDFILE "Source    ObsTime      Duration  Join   //      H(f)\n";
print ROUNDFILE "--------------------------------------------------------------------\n";

print FLATFILE "----------------------------------------------\n";
print FLATFILE "Term\tBegDate\tBegTime\tEndDate\tEndTime\n";
print FLATFILE "----------------------------------------------\n";
printf FLATFILE "set\t%0d.%02d.%02d %s %0d.%02d.%02d %s\n\n", $timestamp1[4], $M{$timestamp1[1]}+1, 
    $timestamp1[2],  $timestamp1[3], $timestamp2[4], $M{$timestamp2[1]}+1,  $timestamp2[2],  $timestamp2[3];
print FLATFILE "Quota    = SunObs\n";
print FLATFILE "Observer = SunObs\n";
print FLATFILE "Feed     = 3\n";
print FLATFILE "AzF      = S+F\n";
print FLATFILE "Sector   = 6-119F\n";
print FLATFILE "Class    = Horizon\n";
print FLATFILE "Azimuth  = 0:00:00\n\n";
print FLATFILE "-----------------------------------------\n";
print FLATFILE "Source   ObsTime    Duration    Altitude\n";
print FLATFILE "-----------------------------------------\n\n";

print MAINOBSFILE ";----mainobs format------\n";
print MAINOBSFILE ";\n";
print MAINOBSFILE ";date_obs    start_time  regstart      zadanie_file  culm_date   culm_time     object  azimuth  altitude SOL_DEC SOL_RA SOLAR_R SOLAR_P SOLAR_B SOL_VALH\n";
print MAINOBSFILE ";yyyy/mm/dd  hh:mm       hh:mm:ss.sss  file_name     yyyy/mm/dd  hh:mm:ss.sss  name    int      float\n";
print MAINOBSFILE ";\n;\n;\n;\n";
print MAINOBSFILE "[observation]\n";

$weekday1 = '';
if ($vynosfile ne "0") {
    open(VFILE, $vynosfile) || die "������� ���� ������� $vynosfile �� ������!";;
    my @vfile = <VFILE>; # ��������� ��� ������ ����� � ������ @vfile
    foreach  my $line (@vfile) {
        my ($k, $v) = split(/:/, $line);
        $hash{int($k)} = int($v);
        close(VFILE);
    }
}
print @hash;

foreach my $line (@file) {
    $str = $line;
    @ary = $str =~ m#\s*([+-]? *\d+(?:\.\d+)?)#g;
    foreach (@ary) { 
        s#\s+##g; 
        $_ += 0; 
    }
    local($year, $month, $day, $hour, $min, $sec, $azim, $hper_g, $hper_m, $hper_s, 
        $t, $t, $t, $t, $t, $t, $ra_g, $ra_m, $ra_s, , $dec_g, $dec_m, $dec_s, 
        $t, $t, $t, $t, $t, $t, $t, $t, $valh, $solar_r, $tmp, $solar_b, $solar_p) = @ary;

    ## Patch to fix Efrat 1-hour issue
    my $posixtime = timelocal($sec, $min, $hour, $day, $month - 1, $year);
    $posixtime -= 3600;
    ($sec, $min, $hour, $day, $month, $year) = (localtime($posixtime))[0, 1, 2, 3, 4, 5];
    $month += 1;
    $year += 1900;

    if ($dec_g gt 0) {
        $dec = $dec_g + $dec_m / 60.0 + $dec_s / 3600.0;
    } else {
        $dec = $dec_g - $dec_m / 60.0 - $dec_s / 3600.0;
    }
    $ra = $ra_g + $ra_m / 60.0 + $ra_s / 3600.0;
    if ($solar_p gt 300) {
        $solar_p = $solar_p - 360.0;
    }

    if ($sec - 59. ge 0 ) {
        $sec = sprintf("%.f", $sec);
    }
    if ($sec - 60.0 ge 0 ) {
        $sec = $sec - 60.0; 
        $min++;
    }

    $hour = $hour + $perevod;
    if ($hour lt 0 ) {
        $hour = $hour + 24;
    }

    # vynos#############
    if ($vynosfile ne "0") {
        if ($debug gt 0) {
            print "\n$azim, $hper_g:$hper_m  + $hash{int($azim)}=";
        }

        $hper_m = $hper_m + $hash{int($azim)};
        if ($hper_m ge 60) {
            $hper_m=$hper_m-60;
            $hper_g++;
        }
        if ($hper_m lt 0) {
            $hper_m=60+$hper_m;
            $hper_g--;
        }

        if ($debug gt 0) {
            print "$hper_g:$hper_m\n";
        }
    }
    #vynos#########

    #print "$sec, $min, $hour,\n";
    $time = timelocal($sec, $min, $hour, $day, $month-1, $year);
    @timestamp = split(/\s+/, localtime($time));

    $weekday2 = $weekday1;
    $weekday1 = $W{$timestamp[0]};
    if ($weekday1 ne $weekday2) {
        if ($weekday2 ne '') {
            print ROUNDFILE "\n";
            print FLATFILE "\n";
        }

        print ROUNDFILE "//$W{$timestamp[0]}\n";
        print FLATFILE "//$W{$timestamp[0]}\n";
        printf ROUNDFILE "ObsDate = %0d.%02d.%02d\n\n",  $timestamp[4], $M{$timestamp[1]}+1, $timestamp[2];
        printf FLATFILE "ObsDate = %0d.%02d.%02d\n\n",  $timestamp[4], $M{$timestamp[1]}+1, $timestamp[2];

        # pervyj moment v zadanii
        my $time_roof_open1 = $time - $beg_mainobs1 * 60.0 - $beg_mainobs2 * 60 
                - $beg_mainobs2_sec - $beg_mainobs_roof * 60.0;
        my $time_roof_open1_minus_hour = $time_roof_open1 - 3600;

        my @t_roof_open1 = split(/\s+/, localtime($time_roof_open1));
        my @t_roof_open1_minus_hour = split(/\s+/, localtime($time_roof_open1_minus_hour));
        # ML
        #my @t_roof_open1 = split(/\s+/,
        #    localtime($time - $beg_mainobs1 * 60.0 - $beg_mainobs2 * 60 
        #        - $beg_mainobs2_sec - $beg_mainobs_roof * 60.0));
        my @t_gsh_mom1 = split(/\s+/,
            localtime($time - $beg_mainobs1 * 60.0 - ($beg_mainobs2 - $beg_mainobs_gsh) * 60
                - $beg_mainobs2_sec - $beg_mainobs_roof * 60.0));

        # vtoroj moment
        my @t_roof_open2 = split(/\s+/,
            localtime($time - $beg_mainobs2 * 60 - $beg_mainobs2_sec - $beg_mainobs_roof * 60.0));
        my @t_gsh_mom2 = split(/\s+/,
            localtime($time - ($beg_mainobs2 - $beg_mainobs_gsh) * 60 
                - $beg_mainobs2_sec - $beg_mainobs_roof*60.0));
        
        #my $sec3=$sec+ $beg_mainobs2_sec;


        printf MAINOBSFILE "%s", $roofclose; #";%d/%02d/%02d %s %s%06.3f %s %d/%02d/%02d %s %s\n", $t_roof_close1[4], $M{$t_roof_close1[1]}+1,$t_roof_close1[2], substr($t_roof_close1[3], 0, 5),  substr($t_roof_close2[3], 0, 6),$sec, "roof_close", $t_roof_close2[4], $M{$t_roof_close2[1]}+1,$t_roof_close2[2], substr($t_roof_close2[3], 0, 14), "roof 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0";
        print  MAINOBSFILE ";\n;\n;\n";
        print  MAINOBSFILE ";==================\n";
        printf MAINOBSFILE ";%d %s %4d, %s\n", $day, $timestamp[1], $year, $timestamp[0];
        print  MAINOBSFILE ";==================\n";
        print  MAINOBSFILE ";\n";
        # testovaja zapis! pri mnogoazimutalnyh nbljudenijah perenesti na drugoe vremja (do nachala nabljudenij)
        #printf MAINOBSFILE "%d/%02d/%02d %s %d/%02d/%02d %s\n", $t_roof_open1[4], $M{$t_roof_open1[1]}+1,$t_roof_open1[2], '10:00 10:01:00.000 z_sun_60', $troof_open1[4], $M{$t_roof_open1[1]}+1,$t_roof_open1[2],  ' 10:02:00.000 sunt +40 0.0 0.0 0.0 0.0 0.0 0.0 0.0';

        # ML
        # if the start_time and regstart are in different days 
        # make the start_time == "00:00" of the same day as the regstart
        if ((substr($t_roof_open1[3], 0, 2) - substr($t_roof_open2[3], 0, 2)) > 0) {
            $t_roof_open1[3] = "00:" . substr($t_roof_open2[3], 3, 2);
            $t_roof_open1[2]++;
        }
        
        printf MAINOBSFILE "%d/%02d/%02d %02d%s %02d%s%06.3f %s %02d/%02d/%02d %02d%s%06.3f %s\n", 
            $t_roof_open1_minus_hour[4], $M{$t_roof_open1_minus_hour[1]} + 1, $t_roof_open1_minus_hour[2],  
            substr($t_roof_open1_minus_hour[3], 0, 5), ':00', 
            substr($t_roof_open1_minus_hour[3], 0, 5), ':01:', 0, "z_sun_60", 
            $t_roof_open1_minus_hour[4], $M{$t_roof_open1_minus_hour[1]} + 1, $t_roof_open1_minus_hour[2],  
            substr($t_roof_open1_minus_hour[3], 0, 5), ':02:', 0, 
            "sunt +40 0.0 0.0 0.0 0.0 0.0 0.0 0.0";
            # ML
            #$t_roof_open1[4], $M{$t_roof_open1[1]} + 1, $t_roof_open1[2],  
            #substr($t_roof_open1[3], 0, 5) - 1, ':00', 
            #substr($t_roof_open1[3], 0, 5) - 1, ':01:', 0, "z_sun_60", 
            #substr($t_roof_open1[3], 0, 5) - 1, ':02:', 0, 
            #"sunt +40 0.0 0.0 0.0 0.0 0.0 0.0 0.0";
        printf MAINOBSFILE "%d/%02d/%02d %s %s%06.3f %s %02d/%02d/%02d %s %s\n", 
            $t_roof_open1[4], $M{$t_roof_open1[1]}+1, $t_roof_open1[2], 
            substr($t_roof_open1[3], 0, 5), substr($t_roof_open2[3], 0, 6), $sec, 
            "roof_open", $t_roof_open2[4], $M{$t_roof_open2[1]} + 1, $t_roof_open2[2], 
            substr($t_roof_open2[3], 0, 14), "roof 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0";
        #printf MAINOBSFILE "%d/%02d/%02d %s %s%06.3f %s %d/%02d/%02d %s %s\n", $t_gsh_mom1[4], $M{$t_gsh_mom1[1]}+1,$t_gsh_mom1[2], substr($t_gsh_mom1[3], 0, 5),  substr($t_gsh_mom2[3], 0, 6),$sec, "z_gsh_60", $t_gsh_mom2[4], $M{$t_gsh_mom2[1]}+1,$t_gsh_mom2[2], substr($t_gsh_mom2[3], 0, 14), "gsh 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 ";
    }

    # ML
    # No one knows when the antenna maintenance will be
    #if ($timestamp[0] eq 'Mon'  and $azim ne 0) {
    #    printf ROUNDFILE "//";
    #}
    printf ROUNDFILE "%s%+d\t%02d:%02d:%05.2f\t%s\t%s%+d\t//\t%2d:%02d:%04.1f\n", $object, $azim, $hour, 
        $min, $sec, $duration, $parabola, $azim, $hper_g, $hper_m, $hper_s;
    # ML
    #if ($timestamp[0] eq 'Mon'  and $azim ne 0) {
    #    printf FLATFILE "//";
    #}
    printf FLATFILE "%s%+d\t%02d:%02d:%05.2f\t%s  %2d:%02d:%04.1f\n", $object, $azim, $hour, $min, $sec, 
        $duration, $hper_g, $hper_m, $hper_s;
    my @timestampbeg1 = split(/\s+/, localtime($time - $beg_mainobs1 * 60.0 - $beg_mainobs2 * 60.0));
    my @timestampbeg2 = split(/\s+/, localtime($time - $beg_mainobs2 * 60.0 - $beg_mainobs2_sec));

    my @t_roof_close1 = split(/\s+/, localtime($time - $beg_mainobs1 * 60.0 + $end_mainobs_roof * 60.0));
    my @t_roof_close2 = split(/\s+/, localtime($time + $end_mainobs_roof * 60.0));
    $roofclose = sprintf("%d/%02d/%02d %s %s%06.3f %s %d/%02d/%02d %s %s\n", 
        $t_roof_close1[4], $M{$t_roof_close1[1]}+1,$t_roof_close1[2], 
        substr($t_roof_close1[3], 0, 5),  substr($t_roof_close2[3], 0, 6), 
        $sec, "roof_close", $t_roof_close2[4], $M{$t_roof_close2[1]}+1, $t_roof_close2[2], 
        substr($t_roof_close2[3], 0, 14), "roof 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0");

    # ML
    # assume no maintenance
    #if ($timestamp[0] eq 'Mon' and $azim ne 0) {
    #    printf MAINOBSFILE ";";
    #}

    # ML
    # if the start_time and regstart are in different days 
    # make the start_time == "00:00" of the same day as the regstart
    if ((substr($timestampbeg1[3], 0, 2) - substr($timestampbeg2[3], 0, 2)) > 0) {
        $timestampbeg1[3] = "00:" . substr($timestampbeg1[3], 3, 2);
        $timestampbeg1[2]++;
    }
        
    printf  MAINOBSFILE "%d/%02d/%02d %s %s.%s %s %d/%02d/%02d %02d:%02d:%06.3f %s %+d %9.6f %06.3f %06.3f %06.3f %06.3f %06.3f %06.3f\n", 
        $timestampbeg1[4], $M{$timestampbeg1[1]}+1, $timestampbeg1[2], 
        substr($timestampbeg1[3], 0, 5), substr($timestampbeg2[3], 0, 8),
        substr(sprintf("%06.3f",$sec),3,3), 
        $scenfile,$year, $month, $day, $hour, $min, $sec, 
        $object_lower, $azim, $hper_g + $hper_m / 60.0 + $hper_s / 3600.0, 
        $dec, $ra, $solar_r, $solar_p, $solar_b, $valh;

} ## foreach $line (@myfile)

printf MAINOBSFILE "%s", $roofclose;
close (ROUNDFILE);
close (MAINOBSFILE);
close (FLATFILE);
### That's all, folks!
