import os.path

import pandas as pd

from genbankfilter.Species import Species


class SpeciesQC(Species):
    def __init__(self,
                 path,
                 max_unknowns=200,
                 contigs=3.0,
                 assembly_size=3.0,
                 mash=3.0):
        Species.__init__(self, path)
        self.max_unknowns = max_unknowns
        self.contigs = contigs
        self.assembly_size = assembly_size
        self.mash = mash
        self.criteria = ["unknowns", "contigs", "Assembly_Size", "MASH"]
        # Tolerance values need to be accessible by the string of their name
        # Not sure if this is an optimal solution...
        self.tolerance = {
            "unknowns": max_unknowns,
            "contigs": contigs,
            "Assembly_Size": assembly_size,
            "MASH": mash
        }
        self.failed = {}
        self.med_abs_devs = {}
        self.dev_refs = {}
        self.allowed = {"unknowns": max_unknowns}
        # Enable user defined colors
        self.colors = {
            "unknowns": "red",
            "contigs": "green",
            "MASH": "purple",
            "Assembly_Size": "orange"
        }
        self.label = '{}-{}-{}-{}'.format(
            max_unknowns, contigs, assembly_size, mash)
        # Pretty sure that setting passed to stats will not create a copy
        self.passed = self.stats

    def __str__(self):
        self.message = [
            "Species: {}".format(self.species), "Tolerance Levels:",
            "Unknown bases:  {}".format(self.max_unknowns),
            "Contigs: {}".format(self.contigs),
            "Assembly Size: {}".format(self.assembly_size),
            "MASH: {}".format(self.mash)
        ]
        return '\n'.join(self.message)

    def filter_unknown_bases(self):
        """Filter out genomes with too many unknown bases."""
        self.failed["unknowns"] = self.stats.index[
            self.stats["N_Count"] > self.tolerance["unknowns"]]
        self.passed = self.stats.drop(self.failed["unknowns"])

    def filter_contigs(self):
        # Only look at genomes with > 10 contigs to avoid throwing off the
        # median absolute deviation
        # Extract genomes with < 10 contigs to add them back in later.
        eligible_contigs = self.passed.Contigs[self.passed.Contigs > 10]
        not_enough_contigs = self.passed.Contigs[self.passed.Contigs <= 10]
        # Median absolute deviation - Average absolute difference between
        # number of contigs and the median for all genomes
        # TODO Define separate function for this
        med_abs_dev = abs(eligible_contigs - eligible_contigs.median()).mean()
        self.med_abs_devs["contigs"] = med_abs_dev
        # Define separate function for this
        # The "deviation reference"
        # Multiply
        dev_ref = med_abs_dev * self.contigs
        self.dev_refs["contigs"] = dev_ref
        self.allowed["contigs"] = eligible_contigs.median() + dev_ref
        # self.passed["contigs"] = eligible_contigs[
        #     abs(eligible_contigs - eligible_contigs.median()) <= dev_ref]
        self.failed["contigs"] = eligible_contigs[
            abs(eligible_contigs - eligible_contigs.median()) > dev_ref].index
        eligible_contigs = eligible_contigs[
            abs(eligible_contigs - eligible_contigs.median()) <= dev_ref]
        # Add genomes with < 10 contigs back in
        eligible_contigs = pd.concat([eligible_contigs, not_enough_contigs])
        # We only need the index of passed genomes at this point
        eligible_contigs = eligible_contigs.index
        self.passed = self.passed.loc[eligible_contigs]

    def filter_med_abs_dev(self, criteria):
        """Filter based on median absolute deviation."""
        # Get the median absolute deviation
        med_abs_dev = abs(self.passed[criteria] -
                          self.passed[criteria].median()).mean()
        dev_ref = med_abs_dev * self.tolerance[criteria]
        self.failed[criteria] = self.passed[
            abs(self.passed[criteria] -
                self.passed[criteria].median()) > dev_ref].index
        self.passed = self.passed[
            abs(self.passed[criteria] -
                self.passed[criteria].median()) <= dev_ref]
        # lower = self.passed[criteria].median() - dev_ref
        # upper = self.passed[criteria].median() + dev_ref

    def summary(self):
        summary = ["Filtered genomes",
                   "Unknown Bases: {}".format(len(self.failed["unknowns"])),
                   "Contigs: {}".format(len(self.failed["contigs"])),
                   "Assembly Size: {}".format(
                       len(self.failed["Assembly_Size"])),
                   "MASH: {}".format(len(self.failed["MASH"]))]
        return '\n'.join(summary)

    def base_node_style(self):
        from ete3 import NodeStyle, AttrFace
        nstyle = NodeStyle()
        nstyle["shape"] = "sphere"
        nstyle["size"] = 2
        nstyle["fgcolor"] = "black"
        for n in self.tree.traverse():
            n.set_style(nstyle)
            if not n.name.startswith('Inner'):
                nf = AttrFace('name', fsize=8)
                nf.margin_right = 100
                nf.margin_left = 3
                n.add_face(nf, column=0)
            else:
                n.name = ' '

    def color_clade(self, criteria):
        """Color nodes using ete3 """
        from ete3 import NodeStyle

        for genome in self.failed[criteria]:
            n = self.tree.get_leaves_by_name(genome).pop()
            nstyle = NodeStyle()
            nstyle["fgcolor"] = self.colors[criteria]
            nstyle["size"] = 6
            n.set_style(nstyle)

    # Might be better in a layout function
    def style_and_render_tree(self, file_types=["svg"]):
        from ete3 import TreeStyle, TextFace, CircleFace
        # midpoint root tree
        self.tree.set_outgroup(self.tree.get_midpoint_outgroup())
        ts = TreeStyle()
        title_face = TextFace(self.species, fsize=20)
        ts.title.add_face(title_face, column=0)
        ts.branch_vertical_margin = 10
        ts.show_leaf_name = False
        # Legend
        for k, v in self.colors.items():
            failures = "Filtered: {}".format(len(self.failed[k]))
            failures = TextFace(failures, fgcolor=v)
            failures.margin_bottom = 5
            tolerance = "Tolerance: {}".format(self.tolerance[k])
            tolerance = TextFace(tolerance, fgcolor=v)
            tolerance.margin_bottom = 5
            f = TextFace(k, fgcolor=v)
            f.margin_bottom = 5
            f.margin_right = 40
            cf = CircleFace(3, v, style="sphere")
            cf.margin_bottom = 5
            cf.margin_right = 5
            ts.legend.add_face(f, column=1)
            ts.legend.add_face(cf, column=2)
            ts.legend.add_face(failures, 1)
            ts.legend.add_face(TextFace(""), 2)
            ts.legend.add_face(tolerance, 1)
            ts.legend.add_face(TextFace(""), 2)
        for f in file_types:
            out_tree = os.path.join(
                self.path, 'tree_{}.{}'.format(self.label, f))
            self.tree.render(out_tree, tree_style=ts)
