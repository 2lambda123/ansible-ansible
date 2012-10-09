.. _lineinfile:

lineinfile
``````````````````````````````

.. versionadded:: 0.7

This module will search a file for a line, and ensure that it is present or absent. 
This is primarily useful when you want to change a single line in a file only. For other cases, see the ``copy`` or ``template`` modules. 

.. raw:: html

    <table>
    <tr>
    <th class="head">parameter</th>
    <th class="head">required</th>
    <th class="head">default</th>
    <th class="head">choices</th>
    <th class="head">comments</th>
    </tr>
        <tr>
    <td>state</td>
    <td>no</td>
    <td>present</td>
    <td><ul><li>present</li><li>absent</li></ul></td>
    <td>Whether the line should be there or not.</td>
    </tr>
        <tr>
    <td>name</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The file to modify</td>
    </tr>
        <tr>
    <td>insertafter</td>
    <td>no</td>
    <td>EOF</td>
    <td><ul><li>BOF</li><li>EOF</li></ul></td>
    <td>Used with <code>state=present</code>. If specified, the line will be inserted after the specified regular expression. Two special values are available; <code>BOF</code> for inserting the line at the beginning of the file, and <code>EOF</code> for inserting the line at the end of the file.</td>
    </tr>
        <tr>
    <td>regexp</td>
    <td>yes</td>
    <td></td>
    <td><ul></ul></td>
    <td>The regular expression to look for in the file. For <code>state=present</code>, the pattern to replace. For <code>state=absent</code>, the pattern of the line to remove.</td>
    </tr>
        <tr>
    <td>line</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Required for <code>state=present</code>. The line to insert/replace into the file. Must match the value given to <code>regexp</code>.</td>
    </tr>
        <tr>
    <td>backup</td>
    <td>no</td>
    <td></td>
    <td><ul></ul></td>
    <td>Create a backup file including the timestamp information so you can get the original file back if you somehow clobbered it incorrectly.</td>
    </tr>
        </table>

.. raw:: html

        <p><pre>
    lineinfile name=/etc/selinux/config regexp=^SELINUX= line=SELINUX=disabled
    </pre></p>
        <p><pre>
    lineinfile name=/etc/sudoers state=absent regexp="^%wheel"
    </pre></p>
    <br/>

