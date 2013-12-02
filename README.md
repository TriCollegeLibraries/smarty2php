smarty2php
==========

Takes a first pass at translating smarty templates back to php. Converts if, else, replace variables, sections with loops, some calls like replace but not fancier code. 

Not everything is translated; files still need to be reviewed and finished up. The script attempts to flag smarty lines it can't fully handle with:

    <? /* FIXME: smarty-translation [note] */ ?>

Takes a single argument, the file to convert.
