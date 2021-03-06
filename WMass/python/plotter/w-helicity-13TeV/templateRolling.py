#!/usr/bin/env python

# USAGE: 
# helicity (check binning)
# python w-helicity-13TeV/templateRolling.py shapesFromEmanuele_goodSyst/ -o plots/helicity/templates/fromEmanuele/  -c el -b [-2.5,-2.3,-2.1,-1.9,-1.7,-1.566,-1.4442,-1.3,-1.2,-1.1,-1.0,-0.9,-0.8,-0.7,-0.6,-0.5,-0.4,-0.3,-0.2,-0.1,0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0,1.1,1.2,1.3,1.4442,1.566,1.7,1.9,2.1,2.3,2.5]*[30,31,32,33,34,35,36,37,38,39,40,41,42,43,44,45] --plot-binned-signal -a helicity [--has-inclusive-signal]
# differential cross section (check binning)

# python w-helicity-13TeV/templateRolling.py cards/diffXsec_2018_05_24_diffXsec_GenPtEtaSigBin/ -o plots/diffXsec/templates/diffXsec_2018_05_24_GenPtEtaSigBin/  -c el -b [-2.5,-2.3,-2.1,-1.9,-1.7,-1.566,-1.4442,-1.2,-1.0,-0.8,-0.6,-0.4,-0.2,0,0.2,0.4,0.6,0.8,1.0,1.2,1.4442,1.566,1.7,1.9,2.1,2.3,2.5]*[30,33,36,39,42,45] --plot-binned-signal -a diffXsec [--has-inclusive-signal]

# python w-helicity-13TeV/templateRolling.py cards/diffXsec_2018_06_20_10/ -o plots/diffXsec/templates/diffXsec_2018_06_20_10/ -c el -b cards/diffXsec_2018_06_20_10/binningPtEta.txt --plot-binned-signal -a diffXsec --draw-selected-etaPt 0.75,40.5 --skipSyst



import ROOT, os
from array import array
from make_diff_xsec_cards import getArrayParsingString
from make_diff_xsec_cards import getArrayBinNumberFromValue
from make_diff_xsec_cards import getDiffXsecBinning
from make_diff_xsec_cards import templateBinning
from make_diff_xsec_cards import get_ieta_ipt_from_process_name

import sys
#sys.path.append(os.environ['CMSSW_BASE']+"/src/CMGTools/WMass/python/plotter/")
#from plotUtils.utility import *
sys.path.append(os.getcwd() + "/plotUtils/")
from utility import *


# def getbinning(splitline):
#     bins = splitline[5]
#     if '*' in bins:
#         etabins = list( float(i) for i in bins.replace(' ','').split('*')[0].replace('\'[','').replace(']','').split(',') )
#         ptbins  = list( float(i) for i in bins.replace(' ','').split('*')[1].replace('[','').replace(']\'','').split(',') )
#         nbinseta = len(etabins)-1
#         nbinspt  = len( ptbins)-1
#         binning = [nbinseta, etabins, nbinspt, ptbins]
#     else:
#         bins = bins.replace('\'','')
#         nbinseta = int( bins.split(',')[0] )
#         nbinspt  = int( bins.split(',')[3] )
#         etamin   = float( bins.split(',')[1] )
#         etamax   = float( bins.split(',')[2] )
#         ptmin    = float( bins.split(',')[4] )
#         ptmax    = float( bins.split(',')[5] )
#         binning = [nbinseta, etamin, etamax, nbinspt, ptmin, ptmax]
#     return binning

ROOT.gStyle.SetOptStat(0)
#ROOT.gStyle.SetPadRightMargin(0.13)
ROOT.gROOT.SetBatch()

def roll1Dto2D(h1d, histo):
    for i in xrange(1,h1d.GetNbinsX()+1):
        # histogram bin is numbered starting from 1, so add 1
        xbin = (i - 1) % histo.GetNbinsX() + 1  
        ybin = (i - 1) / histo.GetNbinsX() + 1
        histo.SetBinContent(xbin,ybin,h1d.GetBinContent(i))
    return histo

def dressed2D(h1d,binning,name,title=''):
    if len(binning) == 4:
        n1 = binning[0]; bins1 = array('d', binning[1])
        n2 = binning[2]; bins2 = array('d', binning[3])
        h2_1 = ROOT.TH2F(name, title, n1, bins1, n2, bins2 )
    else:
        n1 = binning[0]; min1 = binning[1]; max1 = binning[2]
        n2 = binning[3]; min2 = binning[4]; max2 = binning[5]
        h2_1 = ROOT.TH2F(name, title, n1, min1, max1, n2, min2, max2)
    h2_backrolled_1 = roll1Dto2D(h1d, h2_1 )
    return h2_backrolled_1


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser(usage="%prog [options] shapesdir")
    parser.add_option('-o','--outdir', dest='outdir', default='.', type='string', help='output directory to save things')
    parser.add_option('-c','--channel', dest='channel', default='el', type='string', help='Channel (el, mu)')
    parser.add_option('-C','--charge', dest='charge', default='plus,minus', type='string', help='Charges to consider')
    parser.add_option('-p','--postfix', dest='postfix', default='', type='string', help='Postfix for input file with shapes (e.g: "_addInclW" in "Wel_plus_shapes_addInclW.root"). Default is ""')
    parser.add_option('-b','--etaPtbinning', dest='etaPtbinning', default='[-2.5,-1.566,-1.4442,0,1.4442,1.566,2.5]*[30,35,40,45]', type='string', help='eta-pt binning for templates. Use -b file=<name> or simply -b <name> to read binning from file <name>. If passing the array, for the moment it is supposed to be the same for reco and gen')
    parser.add_option(     '--noplot', dest="noplot", default=False, action='store_true', help="Do not plot templates (but you can still save them in a root file with option -s)");
    parser.add_option(     '--has-inclusive-signal', dest="hasInclusiveSignal", default=False, action='store_true', help="Use this option if the file already contains the inclusive signal template and you want to plot it as well (obsolete, it refers to the days when I was manually adding inclusive signal to shapes.root file");
    parser.add_option(     '--plot-binned-signal', dest="plotBinnedSignal", default=False, action='store_true', help="Use this option to plot the binned signal templates (should specify with option --analysis if this is a file for rapidity/helicity or differential cross section");
    parser.add_option('-a','--analysis', dest='analysis', default='diffXsec', type='string', help='Which analysis the shapes file belongs to: helicity or diffXsec (default)')
    parser.add_option('-s','--save', dest='outfile_templates', default='templates_2D', type='string', help='pass name of output file to save 2D histograms (charge is automatically appended before extension). No need to specify extension, .root is automatically added')
    parser.add_option(     '--draw-selected-etaPt', dest='draw_selected_etaPt', default='', type='string', help='Only for xsection. Pass pairs of eta,pt: only the corresponding gen bins will be plotted (inclusive signal is still drawn, unless options --noplot is used as well).')
    parser.add_option(     '--draw-all-bins', dest='draw_all_bins', default=False, action='store_true', help='Draw all bins for signal (default is false, it is quite a huge bunch of plots).')
    parser.add_option(     '--skipSyst', dest='skipSyst', default=False, action='store_true', help='Skip histograms for systematics (will not make plots of ratio with nominal, and should save some time)')
    parser.add_option('-r','--syst-ratio-range', dest='syst_ratio_range', default='0.98,1.02', type='string', help='Comma separated pair of floats used to define the range for the syst/nomi ratio. If "template" is passed, the template min and max values are used (it will be different for each template)')
    (options, args) = parser.parse_args()

    ROOT.TH1.SetDefaultSumw2()

    if len(args) < 1:
        parser.print_usage()
        quit()

    channel = options.channel
    if channel not in ["el","mu"]:
        print "Error: unknown channel %s (select 'el' or 'mu')" % channel
        quit()
       
    analysis = options.analysis
    if analysis not in ["helicity", "diffXsec"]:
        print "Warning: analysis not recognized, must be either \"helicity\" or \"diffXsec\""
        quit()

    if options.analysis != "diffXsec" and options.draw_selected_etaPt != '':
        print "Warning: option --select-etaPt is only supported with --analysis diffXsec (but %s passed).\nIt will be ignored." % options.analysis

    outname = options.outdir
    addStringToEnd(outname,"/",notAddIfEndswithMatch=True)
    createPlotDirAndCopyPhp(outname)

    # get eta-pt binning for both reco and gen
    etaPtBinningVec = getDiffXsecBinning(options.etaPtbinning, "reco")
    recoBins = templateBinning(etaPtBinningVec[0],etaPtBinningVec[1])
    etaPtBinningVec = getDiffXsecBinning(options.etaPtbinning, "gen")
    genBins  = templateBinning(etaPtBinningVec[0],etaPtBinningVec[1])

    #following array is used to call function dressed2D()
    binning = [recoBins.Neta, recoBins.etaBins, recoBins.Npt, recoBins.ptBins]

    if options.draw_selected_etaPt != '':
        eta = float(options.draw_selected_etaPt.split(',')[0]) 
        pt  = float(options.draw_selected_etaPt.split(',')[1]) 
        ieta_sel = getArrayBinNumberFromValue(genBins.etaBins,eta)
        ipt_sel = getArrayBinNumberFromValue(genBins.ptBins,pt)
        if ieta_sel < 0 or ipt_sel < 0:
            print "Error: at least one of eta,pt values passed to --select-etaPt is outside the allowed binning. Please check. Exit"
            quit()
        else:
            print "Selecting gen bins ieta,ipt = %d,%d" % (ieta_sel,ipt_sel)

    lepton = "electron" if channel == "el" else "muon"

    charges = options.charge.split(',')

    qcdsyst = ["muR", "muF", "muRmuF", "alphaS"]
    pdfsyst = ["pdf%d" % i for i in range(1,61)]
    allsysts = qcdsyst + pdfsyst + ["wptSlope", "elescale"]
    allsystsUpDn = []
    for x in allsysts:
        allsystsUpDn.append(x+"Up")
        allsystsUpDn.append(x+"Down")
    outnameSyst = outname + "systematics/"
    createPlotDirAndCopyPhp(outnameSyst)

    for charge in charges:
        shapesfile = "{indir}/W{flav}_{ch}_shapes{pf}.root".format(indir=args[0],flav=channel,ch=charge,pf=options.postfix)
        infile = ROOT.TFile(shapesfile, 'read')
        print ""
        print "==> RUNNING FOR CHARGE ",charge

        outfile_templates = options.outfile_templates
        if outfile_templates.endswith(".root"):
            outfile_templates = outfile_templates.replace(".root","_%s.root" % str(charge))
        else:
            outfile_templates = outfile_templates + "_" + str(charge) + ".root"

        full_outfileName = outname + "/" + outfile_templates
        outfile = ROOT.TFile(full_outfileName, 'recreate')
        print "Will save 2D templates in file --> " + full_outfileName

        chs = '+' if charge == 'plus' else '-' 
        adjustSettings_CMS_lumi()

        if options.plotBinnedSignal:
        # doing binned signal
            print "Signal"
            if analysis == "helicity":                
                for pol in ['right', 'left']:
                    print "\tPOLARIZATION ",pol
                    # at this level we don't know how many bins we have, but we know that, for nominal templates, Ybin will be the second last token if we split the template name on '_' 
                    inclSigName = 'W{ch}_{pol}_W{ch}_{pol}_{flav}_inclusive'.format(ch=charge,pol=pol,flav=channel)
                    inclSigTitle = 'W{chs} {pol} inclusive'.format(pol=pol,chs=chs)
                    hSigInclusive = ROOT.TH2F(inclSigName,inclSigTitle,recoBins.Neta, array('d',recoBins.etaBins), recoBins.Npt, array('d',recoBins.ptBins))

                    for k in infile.GetListOfKeys():
                        name=k.GetName()
                        obj=k.ReadObj()
                        signalMatch = "{ch}_{pol}_{flav}_Ybin_".format(ch=charge,pol=pol,flav=channel)                        
                        # name.split('_')[-2] == "Ybin" : this excludes systematics
                        if obj.InheritsFrom("TH1") and signalMatch in name and name.split('_')[-2] == "Ybin":

                            ## need to implement a way of getting the rapidity binning    
                            # jobsdir = args[0]+'/jobs/'
                            # jobfile_name = 'W{ch}_{flav}_Ybin_{b}.sh'.format(ch=charge,flav=channel,b=ybin)
                            # tmp_jobfile = open(jobsdir+jobfile_name, 'r')
                            # tmp_line = tmp_jobfile.readlines()[-1].split()
                            # ymin = list(i for i in tmp_line if '(genw_y)>' in i)[0].replace('\'','').split('>')[-1]
                            # ymax = list(i for i in tmp_line if '(genw_y)<' in i)[0].replace('\'','').split('<')[-1]                            
                            ymin = "X" # dummy for the moment
                            ymax = "Y"
                            ybin = name.split('_')[-1]
                            name2D = 'W{ch}_{pol}_W{ch}_{pol}_{flav}_Ybin_{ybin}'.format(ch=charge,pol=pol,flav=channel,ybin=ybin)
                            title2D = 'W{chs} {pol} : |Yw| #in [{ymin},{ymax})'.format(ymin=ymin,ymax=ymax,pol=pol,ybin=ybin,chs=chs)
                            h2_backrolled_1 = dressed2D(obj,binning,name2D,title2D)
                            h2_backrolled_1.Write(name2D)
                            hSigInclusive.Add(h2_backrolled_1)

                            if options.draw_all_bins: drawThisBin = True
                            else: drawThisBin = False

                            if not options.noplot and drawThisBin:
                                xaxisTitle = '%s #eta' % lepton
                                yaxisTitle = '%s p_{T} [GeV]' % lepton
                                zaxisTitle = "Events::0,%.1f" % h2_backrolled_1.GetMaximum()
                                drawCorrelationPlot(h2_backrolled_1, 
                                                    xaxisTitle, yaxisTitle, zaxisTitle, 
                                                    'W_{ch}_{pol}_{flav}_Ybin_{ybin}'.format(ch=charge,pol=pol,flav=channel,ybin=ybin),
                                                    "ForceTitle",outname,1,1,False,False,False,1)

                    hSigInclusive.Write()
                    if not options.noplot:
                        xaxisTitle = '%s #eta' % lepton
                        yaxisTitle = '%s p_{T} [GeV]' % lepton
                        zaxisTitle = "Events::0,%.1f" % hSigInclusive.GetMaximum()
                        drawCorrelationPlot(hSigInclusive, 
                                            xaxisTitle, yaxisTitle, zaxisTitle, 
                                            'W_{ch}_{pol}_{flav}_inclusive'.format(ch=charge,pol=pol,flav=channel),
                                            "ForceTitle",outname,1,1,False,False,False,1)
                                                
            else:  

                inclSigName = 'W{ch}_{flav}_inclusive'.format(ch=charge,flav=channel)
                inclSigTitle = 'W{chs} inclusive'.format(chs=chs)
                hSigInclusive = ROOT.TH2F(inclSigName,inclSigTitle,recoBins.Neta, array('d',recoBins.etaBins), recoBins.Npt, array('d',recoBins.ptBins))
                hSigInclusive_syst = {}
                if not options.skipSyst:
                    for systvar in allsystsUpDn:
                        sysName  = inclSigName  + "_" + systvar
                        sysTitle = inclSigTitle + "_" + systvar
                        hSigInclusive_syst[systvar] = ROOT.TH2F(sysName,sysTitle,recoBins.Neta, array('d',recoBins.etaBins), recoBins.Npt, array('d',recoBins.ptBins))

                # diff cross section
                for k in infile.GetListOfKeys():
                    name=k.GetName()
                    obj=k.ReadObj()
                    # example of name in shapes.root: x_Wplus_el_ieta_3_ipt_0_Wplus_el_group_0
                    # example of name in shapes.root: x_Wplus_mu_outliers_Wplus_mu_outliers_group_37
                    signalMatch = "{ch}_{flav}_".format(ch=charge,flav=channel)                      
                    # name.split('_')[-2] == "group" : this condition excludes systematics

                    if obj.InheritsFrom("TH1") and signalMatch in name:

                        if name.split('_')[-2] == "group":

                            if "outliers" in name:
                                drawThisBin = True
                                name2D = 'W{ch}_{flav}_outliers'.format(ch=charge,flav=channel)
                                title2D = 'W{chs}: |#eta| > {etamax}#; p_{{T}} #notin [{ptmin:.0f},{ptmax:.0f})'.format(etamax=genBins.etaBins[-1],
                                                                                                                        ptmin=genBins.ptBins[0],
                                                                                                                        ptmax=genBins.ptBins[-1],
                                                                                                                        chs=chs)
                            else:
                                etabinIndex,ptbinIndex = get_ieta_ipt_from_process_name(name)
                                if options.draw_all_bins: drawThisBin = True
                                elif options.draw_selected_etaPt != '':
                                    if etabinIndex != ieta_sel or ptbinIndex != ipt_sel: drawThisBin = False                            
                                    else: drawThisBin = True
                                else: drawThisBin = False
                                name2D = 'W{ch}_{flav}_ieta_{ieta}_ipt_{ipt}'.format(ch=charge,flav=channel,ieta=etabinIndex,ipt=ptbinIndex)
                                title2D = 'W{chs}: |#eta| #in [{etamin},{etamax})#; p_{{T}} #in [{ptmin:.0f},{ptmax:.0f})'.format(etamin=genBins.etaBins[etabinIndex],
                                                                                                                                  etamax=genBins.etaBins[etabinIndex+1],
                                                                                                                                  ptmin=genBins.ptBins[ptbinIndex],
                                                                                                                                  ptmax=genBins.ptBins[ptbinIndex+1],
                                                                                                                                  chs=chs)

                            h2_backrolled_1 = dressed2D(obj,binning,name2D,title2D)
                            h2_backrolled_1.Write(name2D)
                            hSigInclusive.Add(h2_backrolled_1)

                            if not options.noplot and drawThisBin:
                                xaxisTitle = '%s #eta' % lepton
                                yaxisTitle = '%s p_{T} [GeV]' % lepton
                                zaxisTitle = "Events::0,%.1f" % h2_backrolled_1.GetMaximum()
                                drawCorrelationPlot(h2_backrolled_1, 
                                                    xaxisTitle, yaxisTitle, zaxisTitle, 
                                                    h2_backrolled_1.GetName(),
                                                    "ForceTitle",outname,1,1,False,False,False,1)

                        elif not options.skipSyst:
                            h2_backrolled_1 = dressed2D(obj,binning,name+"_tmp","")                            
                            systvar = name.split('_')[-1]
                            hSigInclusive_syst[systvar].Add(h2_backrolled_1)
                            
                hSigInclusive.Write()
                if not options.noplot:
                    xaxisTitle = '%s #eta' % lepton
                    yaxisTitle = '%s p_{T} [GeV]' % lepton
                    zaxisTitle = "Events::0,%.1f" % hSigInclusive.GetMaximum()
                    drawCorrelationPlot(hSigInclusive, 
                                        xaxisTitle, yaxisTitle, zaxisTitle, 
                                        hSigInclusive.GetName(),
                                        "ForceTitle",outname,1,1,False,False,False,1)
                    if not options.skipSyst:
                        for systvar in allsystsUpDn:
                            hSigInclusive_syst[systvar].Divide(hSigInclusive)
                            if options.syst_ratio_range == "template":
                                zaxisTitle = "Events::%.1f,%.1f" % (hSigInclusive_syst[systvar].GetMinimum(),hSigInclusive_syst[systvar].GetMaximum())
                            else:
                                ratiomin = options.syst_ratio_range.split(',')[0]
                                ratiomax = options.syst_ratio_range.split(',')[1]
                            zaxisTitle = "Events::%s,%s" % (ratiomin,ratiomax)
                            drawCorrelationPlot(hSigInclusive_syst[systvar], 
                                                xaxisTitle, yaxisTitle, zaxisTitle, 
                                                "systOverNorm_"+hSigInclusive_syst[systvar].GetName(),
                                                "ForceTitle",outnameSyst,1,1,False,False,False,1)


        # do backgrounds and, if requested, inclusive signal
        print "Backgrounds" + (" and inclusive signal" if options.hasInclusiveSignal else "")
        procs=["Flips","Z","Top","DiBosons","TauDecaysW","data_fakes"]
        titles=["charge flips","DY","Top","di-bosons","W#rightarrow#tau#nu","QCD"]
        if options.hasInclusiveSignal: 
            procs.append("W{ch}_{flav}".format(ch=charge,flav=channel))
            signalTitle = "W^{%s}#rightarrow%s#nu" % (chs, "e" if channel == "el" else "#mu")
            titles.append(signalTitle)

        for i,p in enumerate(procs):
            h1_1 = infile.Get('x_{p}'.format(p=p))
            if not h1_1: continue # muons don't have Flips components
            h2_backrolled_1 = dressed2D(h1_1,binning,p,titles[i])
            h2_backrolled_1.Write(str(p))
            
            xaxisTitle = '%s #eta' % lepton
            yaxisTitle = '%s p_{T} [GeV]' % lepton
            zaxisTitle = "Events::0,%.1f" % h2_backrolled_1.GetMaximum()

            if not options.noplot:
                drawCorrelationPlot(h2_backrolled_1, 
                                    xaxisTitle, yaxisTitle, zaxisTitle, 
                                    '{proc}_{ch}_{flav}'.format(proc=p,ch=charge,flav=channel),
                                    "ForceTitle",outname,1,1,False,False,False,1)

            # canv = ROOT.TCanvas()
            # h2_backrolled_1.Draw('colz')
            # if not options.noplot:
            #     for ext in ['pdf', 'png']:
            #         canv.SaveAs('{odir}/{proc}_{ch}_{flav}.{ext}'.format(odir=outname,proc=p,ch=charge,flav=channel,ext=ext))
            
        outfile.Close()

    ## canv.Divide(1,2)
    ## canv.cd(1)
    ## h2.Draw('colz')
    ## canv.cd(2)
    ## h2backrolled.Draw('colz')
